import React, { useCallback, useEffect, useMemo, useState } from "react";
import { fetchQuiz, fetchQuizLevels, fetchQuizList, submitQuizAttempt } from "../../api/client.js";
import { useOnlineStatus } from "../../hooks/useOnlineStatus.js";
import "./ui.css";
import "./QuizPractice.css";

const LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"];
const LEVEL_NAMES = { A1: "Boshlang'ich", A2: "Elementar", B1: "O'rta", B2: "O'rtadan yuqori", C1: "Yuqori", C2: "Mukammal" };
const CATEGORIES = [
  { key: "", label: "Hammasi" },
  { key: "grammar", label: "Grammatika" },
  { key: "vocabulary", label: "So'z boyligi" },
];
const PENDING_KEY = "st_quiz_pending_attempts_v1";
const quizCacheKey = id => `st_quiz_${id}`;

const safeGet = (k, fallback) => { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : fallback; } catch { return fallback; } };
const safeSet = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* xotira to'lgan */ } };

export default function QuizPractice() {
  const { isOnline } = useOnlineStatus();
  const [levels, setLevels] = useState(null);
  const [myLevel, setMyLevel] = useState(null);
  const [level, setLevel] = useState(null);
  const [category, setCategory] = useState("");
  const [list, setList] = useState(null);
  const [error, setError] = useState("");
  const [active, setActive] = useState(null);   // to'liq quiz (savollar bilan)
  const [pending, setPending] = useState(() => safeGet(PENDING_KEY, []).length);

  useEffect(() => {
    fetchQuizLevels()
      .then(d => {
        setLevels(d.levels);
        setMyLevel(d.my_level);
        setLevel(d.my_level || d.levels.find(l => l.total)?.level || "A1");
      })
      .catch(() => { setLevel("A1"); setLevels(LEVELS.map(l => ({ level: l, total: 0, passed: 0 }))); });
  }, []);

  const loadList = useCallback(() => {
    if (!level) return;
    setList(null);
    setError("");
    fetchQuizList({ level, category })
      .then(setList)
      .catch(e => setError(e.isNetworkError ? "Internet yo'q. Avval ochilgan quizlarni offline yechish mumkin." : e.message));
  }, [level, category]);
  useEffect(loadList, [loadList]);

  // Offline paytda yechilgan natijalarni internet qaytganda yuborish
  useEffect(() => {
    if (!isOnline) return;
    const queue = safeGet(PENDING_KEY, []);
    if (!queue.length) return;
    (async () => {
      const left = [];
      for (const item of queue) {
        try { await submitQuizAttempt(item.quizId, item.answers); } catch { left.push(item); }
      }
      safeSet(PENDING_KEY, left);
      setPending(left.length);
      if (left.length < queue.length) loadList();
    })();
  }, [isOnline, loadList]);

  async function open(q) {
    setError("");
    try {
      const full = await fetchQuiz(q.id);
      safeSet(quizCacheKey(q.id), full);
      setActive(full);
    } catch (e) {
      const cached = safeGet(quizCacheKey(q.id), null);
      if (cached) setActive(cached);
      else setError("Bu quizni ochib bo'lmadi. Internetni tekshiring.");
    }
  }

  const nextQuiz = useMemo(() => {
    if (!active || !list) return null;
    const i = list.findIndex(q => q.id === active.id);
    return list.slice(i + 1).find(q => (q.best_score ?? 0) < 70) || null;
  }, [active, list]);

  if (active) {
    return (
      <div className="ui quiz">
        <QuizRunner
          key={active.id}
          quiz={active}
          onExit={() => { setActive(null); loadList(); }}
          onNext={nextQuiz ? () => open(nextQuiz) : null}
          onQueued={() => setPending(safeGet(PENDING_KEY, []).length)}
        />
      </div>
    );
  }

  const levelInfo = levels?.find(l => l.level === level);
  const grouped = groupByCategory(list || []);

  return (
    <div className="ui quiz">
      <header className="ui-head">
        <div>
          <h1>Quiz</h1>
          <p>Darajangizga mos testlar. 70% va undan yuqori natija bo'lim o'tilgan deb hisoblanadi.</p>
        </div>
      </header>

      {pending > 0 && <div className="ui-alert" style={{ marginBottom: 14 }}>{pending} ta natija internet qaytganda yuboriladi.</div>}

      <nav className="quiz-levels" aria-label="Daraja">
        {(levels || LEVELS.map(l => ({ level: l }))).filter(l => l.level).map(l => {
          const pct = l.total ? Math.round((l.passed / l.total) * 100) : 0;
          return (
            <button key={l.level} className={"quiz-level" + (level === l.level ? " on" : "")}
              onClick={() => setLevel(l.level)} disabled={levels && !l.total} aria-pressed={level === l.level}>
              <span className="quiz-level-code">{l.level}</span>
              <span className="quiz-level-name">{LEVEL_NAMES[l.level]}</span>
              {l.total > 0 && <span className="quiz-level-bar"><i style={{ width: `${pct}%` }} /></span>}
              {myLevel === l.level && <span className="quiz-level-mine">Sizning darajangiz</span>}
            </button>
          );
        })}
      </nav>

      <div className="quiz-toolbar">
        <div className="ui-chips">
          {CATEGORIES.map(c => (
            <button key={c.key} className={"ui-chip" + (category === c.key ? " on" : "")} onClick={() => setCategory(c.key)}>{c.label}</button>
          ))}
        </div>
        {levelInfo && <span className="ui-faint">{levelInfo.passed} / {levelInfo.total} o'tilgan</span>}
      </div>

      {error && <div className="ui-alert bad">{error}</div>}
      {!list && !error && <div className="quiz-grid">{[0, 1, 2, 3, 4, 5].map(i => <div key={i} className="ui-skeleton" style={{ height: 112 }} />)}</div>}
      {list && !list.length && <div className="ui-card ui-empty"><strong>Bu darajada quiz yo'q</strong>Boshqa daraja yoki turni tanlang.</div>}

      {grouped.map(g => (
        <section key={g.key} className="quiz-section">
          {grouped.length > 1 && <h2>{g.label} <span className="ui-faint">{g.items.length}</span></h2>}
          <div className="quiz-grid">
            {g.items.map(q => <QuizCard key={q.id} q={q} onOpen={() => open(q)} />)}
          </div>
        </section>
      ))}
    </div>
  );
}

function groupByCategory(list) {
  const labels = { grammar: "Grammatika", vocabulary: "So'z boyligi", other: "Boshqa" };
  return ["grammar", "vocabulary", "other"]
    .map(key => ({ key, label: labels[key], items: list.filter(q => q.category === key) }))
    .filter(g => g.items.length);
}

function QuizCard({ q, onOpen }) {
  const best = q.best_score;
  const status = best == null ? "new" : best >= 70 ? "passed" : "retry";
  return (
    <button className={"quiz-card " + status} onClick={onOpen}>
      <span className="quiz-card-title">{q.title.replace(/^[ABC]\d\s+/, "").replace(/^English\s+/, "")}</span>
      <span className="quiz-card-meta">{q.question_count} ta savol</span>
      <span className="quiz-card-foot">
        {status === "new" && <span className="ui-badge">Yangi</span>}
        {status === "passed" && <span className="ui-badge ok">O'tildi · {Math.round(best)}%</span>}
        {status === "retry" && <span className="ui-badge pen">{Math.round(best)}% · qayta urining</span>}
      </span>
    </button>
  );
}

function QuizRunner({ quiz, onExit, onNext, onQueued }) {
  const questions = quiz.questions || [];
  const [idx, setIdx] = useState(0);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [saving, setSaving] = useState(false);
  const q = questions[idx];
  const chosen = q ? answers[q.id] : undefined;
  const revealed = chosen !== undefined;

  const choose = useCallback(ci => {
    if (!q || answers[q.id] !== undefined) return;
    setAnswers(a => ({ ...a, [q.id]: ci }));
  }, [q, answers]);

  const finish = useCallback(async () => {
    const correct = questions.filter(x => answers[x.id] === x.correct_index).length;
    const local = { correct, total: questions.length, score: Math.round((correct / Math.max(1, questions.length)) * 100) };
    setSaving(true);
    try {
      const res = await submitQuizAttempt(quiz.id, answers);
      setResult({ ...local, points: res.earned_points, streak: res.streak });
    } catch {
      const queue = safeGet(PENDING_KEY, []);
      queue.push({ quizId: quiz.id, answers, savedAt: Date.now() });
      safeSet(PENDING_KEY, queue);
      onQueued();
      setResult({ ...local, offline: true });
    } finally {
      setSaving(false);
    }
  }, [answers, questions, quiz.id, onQueued]);

  const next = useCallback(() => {
    if (idx + 1 < questions.length) setIdx(i => i + 1);
    else finish();
  }, [idx, questions.length, finish]);

  useEffect(() => {
    const onKey = e => {
      if (result) return;
      if (["1", "2", "3", "4"].includes(e.key)) choose(Number(e.key) - 1);
      if (e.key === "Enter" && revealed) next();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [choose, next, revealed, result]);

  function speak(text) {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "en-US"; u.rate = 0.92;
    window.speechSynthesis.speak(u);
  }

  if (!questions.length) {
    return <div className="ui-card ui-empty"><strong>Bu quizda savol yo'q</strong><button className="ui-btn" onClick={onExit}>Orqaga</button></div>;
  }

  if (result) {
    const wrong = questions.filter(x => answers[x.id] !== x.correct_index);
    return (
      <div className="quiz-result">
        <div className="ui-card quiz-result-card">
          <span className={"quiz-result-score" + (result.score >= 70 ? " ok" : "")}>{result.score}%</span>
          <h2>{result.score >= 90 ? "A'lo natija!" : result.score >= 70 ? "Bo'lim o'tildi" : "Yana bir urinib ko'ring"}</h2>
          <p className="ui-muted">{result.correct} / {result.total} to'g'ri
            {result.points > 0 && ` · +${result.points} ball`}
            {result.offline && " · natija internet qaytganda yuboriladi"}</p>
          <div className="quiz-result-actions">
            <button className="ui-btn" onClick={onExit}>Ro'yxatga qaytish</button>
            {result.score < 70 && <button className="ui-btn" onClick={() => { setAnswers({}); setIdx(0); setResult(null); }}>Qayta yechish</button>}
            {onNext && <button className="ui-btn primary" onClick={onNext}>Keyingi quiz</button>}
          </div>
        </div>
        {wrong.length > 0 && (
          <div className="ui-card">
            <h2 style={{ marginBottom: 12 }}>Xatolar ustida ishlash</h2>
            <ul className="quiz-review">
              {wrong.map(x => (
                <li key={x.id}>
                  <p>{x.text}</p>
                  <p><span className="quiz-review-bad">{answers[x.id] !== undefined ? x.choices[answers[x.id]] : "javob berilmagan"}</span>
                    {" → "}<span className="quiz-review-ok">{x.choices[x.correct_index]}</span></p>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="quiz-runner">
      <div className="quiz-runner-top">
        <button className="ui-btn sm" onClick={onExit} aria-label="Quizdan chiqish">Chiqish</button>
        <div className="quiz-runner-progress" aria-label={`${idx + 1} / ${questions.length}`}>
          {questions.map((x, i) => (
            <i key={x.id} className={
              answers[x.id] === undefined ? (i === idx ? "now" : "") : answers[x.id] === x.correct_index ? "ok" : "bad"} />
          ))}
        </div>
        <span className="ui-faint">{idx + 1}/{questions.length}</span>
      </div>

      <div className="ui-card quiz-q">
        <p className="quiz-q-level">{quiz.level || ""} · {quiz.title}</p>
        <h2 className="quiz-q-text">
          {q.text}
          <button className="quiz-speak" onClick={() => speak(q.text)} aria-label="Savolni eshitish">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M11 5 6 9H2v6h4l5 4V5Z" /><path d="M15.5 8.5a5 5 0 0 1 0 7M19 5a10 10 0 0 1 0 14" /></svg>
          </button>
        </h2>
        <div className="quiz-options" role="radiogroup">
          {q.choices.map((c, ci) => {
            let cls = "quiz-option";
            if (revealed) {
              if (ci === q.correct_index) cls += " correct";
              else if (ci === chosen) cls += " wrong";
              else cls += " dim";
            }
            return (
              <button key={ci} className={cls} onClick={() => choose(ci)} disabled={revealed} role="radio" aria-checked={chosen === ci}>
                <kbd>{ci + 1}</kbd><span>{c}</span>
              </button>
            );
          })}
        </div>
        {revealed && (
          <div className={"quiz-feedback " + (chosen === q.correct_index ? "ok" : "bad")} aria-live="polite">
            <span>{chosen === q.correct_index ? "To'g'ri!" : <>To'g'ri javob: <strong>{q.choices[q.correct_index]}</strong></>}</span>
            <button className="ui-btn primary" onClick={next} disabled={saving} autoFocus>
              {idx + 1 < questions.length ? "Keyingi" : saving ? "Saqlanmoqda..." : "Natijani ko'rish"}
            </button>
          </div>
        )}
      </div>
      <p className="ui-faint quiz-keys">Klaviatura: 1–4 javob tanlash, Enter — keyingi savol</p>
    </div>
  );
}
