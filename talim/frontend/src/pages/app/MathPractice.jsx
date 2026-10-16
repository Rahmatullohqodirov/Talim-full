import React, { useEffect, useMemo, useRef, useState } from "react";
import { explainMathProblem, fetchMathProblems, fetchMathProgress, submitMathAnswer } from "../../api/client.js";
import RichText from "./RichText.jsx";
import "./ui.css";
import "./MathPractice.css";

const DIFF = { 1: "Oson", 2: "O'rta", 3: "Qiyin" };
const KEYS = ["x", "²", "√", "π", "/", "-", ";"];

// "x^2" -> "x²", "pi" -> "π", "*" -> "·" — masala matnini o'qishga qulay qiladi
function pretty(text) {
  return String(text || "")
    .replace(/\^2\b/g, "²").replace(/\^3\b/g, "³")
    .replace(/\bpi\b/g, "π").replace(/sqrt\(([^)]+)\)/g, "√$1")
    .replace(/(\d)\s*\*\s*(\d)/g, "$1 · $2");
}

export default function MathPractice() {
  const [problems, setProblems] = useState(null);
  const [progress, setProgress] = useState([]);
  const [topic, setTopic] = useState("");
  const [diff, setDiff] = useState(0);
  const [current, setCurrent] = useState(null);
  const [error, setError] = useState("");
  const [session, setSession] = useState({ correct: 0, total: 0, points: 0 });

  function load() {
    Promise.all([fetchMathProblems(), fetchMathProgress().catch(() => [])])
      .then(([p, pr]) => { setProblems(p?.results || p || []); setProgress(pr || []); })
      .catch(e => setError(e.isNetworkError ? "Internet yo'q." : e.message || "Masalalarni yuklab bo'lmadi."));
  }
  useEffect(load, []);

  const list = useMemo(() => (problems || []).filter(p =>
    (!topic || p.topic_name === topic) && (!diff || p.difficulty === diff)), [problems, topic, diff]);

  const nextProblem = useMemo(() => {
    if (!current) return list.find(p => !p.solved) || list[0] || null;
    const i = list.findIndex(p => p.id === current.id);
    const rest = [...list.slice(i + 1), ...list.slice(0, i)];
    return rest.find(p => !p.solved) || rest[0] || null;
  }, [list, current]);

  // Ko'rsatilayotgan masalani "qotirib" qo'yamiz: yechilgach ro'yxat o'zgarsa ham, "Keyingi" bosilmaguncha almashmaydi
  useEffect(() => {
    if (problems && (!current || !list.some(p => p.id === current.id)) && nextProblem) setCurrent(nextProblem);
  }, [problems, list, current, nextProblem]);

  function onResult(problem, res) {
    setSession(s => ({ correct: s.correct + (res.is_correct ? 1 : 0), total: s.total + 1, points: s.points + (res.points || 0) }));
    if (res.is_correct) {
      setProblems(ps => ps.map(p => (p.id === problem.id ? { ...p, solved: true, tried: true } : p)));
      setProgress(pr => pr.map(t => (t.name === problem.topic_name && !problem.solved ? { ...t, solved: t.solved + 1 } : t)));
    }
  }

  const totals = progress.reduce((a, t) => ({ total: a.total + t.total, solved: a.solved + t.solved }), { total: 0, solved: 0 });

  return (
    <div className="ui mp">
      <header className="ui-head">
        <div>
          <h1>Matematika</h1>
          <p>Masalani yeching va javobni yozing. Qiynalsangiz, avval maslahat oling, keyin yechimni yoki AI tushuntirishini ko'ring.</p>
        </div>
        {session.total > 0 && (
          <div className="mp-session">
            <strong>{session.correct}/{session.total}</strong> to'g'ri{session.points ? ` · +${session.points} ball` : ""}
          </div>
        )}
      </header>

      {error && <div className="ui-alert bad">{error}</div>}

      <div className="mp-grid">
        <aside className="ui-card mp-topics">
          <h2>Mavzular</h2>
          <p className="ui-faint">{totals.solved} / {totals.total} yechilgan</p>
          <ul>
            <li>
              <button className={!topic ? "on" : ""} onClick={() => { setTopic(""); setCurrent(null); }}>
                <span>Hammasi</span><span className="ui-faint">{problems?.length || 0}</span>
              </button>
            </li>
            {progress.map(t => (
              <li key={t.id}>
                <button className={topic === t.name ? "on" : ""} onClick={() => { setTopic(t.name); setCurrent(null); }}>
                  <span>{t.name}</span>
                  <span className="mp-topic-count">{t.solved}/{t.total}</span>
                  <span className="mp-topic-bar"><i style={{ width: `${t.total ? (t.solved / t.total) * 100 : 0}%` }} /></span>
                </button>
              </li>
            ))}
          </ul>
          <div className="ui-tabs mp-diff" aria-label="Qiyinlik">
            {[0, 1, 2, 3].map(d => <button key={d} className={diff === d ? "on" : ""} onClick={() => { setDiff(d); setCurrent(null); }}>{d ? DIFF[d] : "Barchasi"}</button>)}
          </div>
        </aside>

        <section className="mp-main">
          {!problems && !error && <div className="ui-skeleton" style={{ height: 360 }} />}
          {problems && !list.length && <div className="ui-card ui-empty"><strong>Bu filtr bo'yicha masala yo'q</strong>Boshqa mavzu yoki qiyinlikni tanlang.</div>}
          {problems && list.length > 0 && (
            <Problem key={current?.id} problem={current}
              index={list.findIndex(p => p.id === current?.id)} count={list.length}
              onResult={onResult} onNext={() => nextProblem && setCurrent(nextProblem)} />
          )}
          {problems && list.length > 1 && (
            <div className="mp-strip" aria-label="Masalalar">
              {list.map((p, i) => (
                <button key={p.id} className={(p.solved ? "solved " : p.tried ? "tried " : "") + (current?.id === p.id ? "on" : "")}
                  onClick={() => setCurrent(p)} title={pretty(p.statement)}>{i + 1}</button>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

function Problem({ problem, index, count, onResult, onNext }) {
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState(null);   // {is_correct, answers, attempt_number, needs_self_check}
  const [hint, setHint] = useState(false);
  const [steps, setSteps] = useState(false);
  const [ai, setAi] = useState(null);
  const [busy, setBusy] = useState(false);
  const started = useRef(Date.now());
  const inputRef = useRef(null);
  if (!problem) return null;
  const isSelf = problem.answer_type === "self";

  async function check(selfCorrect) {
    if (!isSelf && !answer.trim()) { inputRef.current?.focus(); return; }
    setBusy(true);
    try {
      const body = { user_answer: answer, time_spent_seconds: Math.round((Date.now() - started.current) / 1000) };
      if (selfCorrect !== undefined) body.self_correct = selfCorrect;
      const res = await submitMathAnswer(problem.id, body);
      if (res.needs_self_check) { setSteps(true); setResult({ needs_self_check: true }); return; }
      setResult(res);
      onResult(problem, res);
    } catch (e) {
      setResult({ error: e.message || "Tekshirib bo'lmadi." });
    } finally {
      setBusy(false);
    }
  }

  async function explain() {
    setAi({ loading: true });
    try { const r = await explainMathProblem(problem.id); setAi({ text: r.explanation }); }
    catch (e) { setAi({ text: e.message || "AI hozir javob bera olmadi." }); }
  }

  function insert(k) {
    const map = { "²": "^2", "√": "√", "π": "π" };
    setAnswer(a => a + (map[k] || k));
    inputRef.current?.focus();
  }

  const correct = result?.is_correct === true;
  const wrong = result?.is_correct === false;

  return (
    <article className="ui-card mp-problem">
      <div className="mp-meta">
        <span className="ui-badge accent">{problem.topic_name}</span>
        <span className={"ui-badge mp-d" + problem.difficulty}>{DIFF[problem.difficulty] || problem.difficulty_label}</span>
        {problem.solved && <span className="ui-badge ok">Yechilgan</span>}
        <span className="ui-faint mp-count">{index + 1} / {count}</span>
      </div>
      <h2 className="mp-statement">{pretty(problem.statement)}</h2>

      {!isSelf ? (
        <>
          <div className={"mp-answer" + (correct ? " ok" : wrong ? " bad" : "")}>
            <span className="mp-answer-label">Javob</span>
            <input ref={inputRef} value={answer} onChange={e => { setAnswer(e.target.value); if (wrong) setResult(null); }}
              onKeyDown={e => e.key === "Enter" && !correct && check()} placeholder="masalan: 4 yoki 2; 3" disabled={correct}
              inputMode="decimal" autoComplete="off" aria-label="Javobingiz" autoFocus />
            <button className="ui-btn primary" onClick={() => check()} disabled={busy || correct}>{busy ? "..." : "Tekshirish"}</button>
          </div>
          <div className="mp-keys" aria-label="Belgilar">
            {KEYS.map(k => <button key={k} onClick={() => insert(k)} disabled={correct} type="button">{k}</button>)}
          </div>
        </>
      ) : (
        <p className="ui-muted">Bu masala isbot yoki izoh talab qiladi. Daftaringizda yeching, keyin yechim bilan solishtiring.</p>
      )}

      {result?.error && <div className="ui-alert bad">{result.error}</div>}
      {correct && (
        <div className="mp-feedback ok" role="status">
          <strong>To'g'ri!</strong>{result.points ? ` +${result.points} ball` : " (bu masala avval yechilgan)"}
          <button className="ui-btn ink" onClick={onNext} autoFocus>Keyingi masala</button>
        </div>
      )}
      {wrong && (
        <div className="mp-feedback bad" role="status">
          <span>{result.answers
            ? <>Noto'g'ri. To'g'ri javob: <strong>{result.answers.join("; ")}</strong>. Yechimni ko'rib chiqing.</>
            : "Hali to'g'ri emas. Maslahatni ko'ring va yana urinib ko'ring."}</span>
          {result.answers && <button className="ui-btn" onClick={onNext}>Keyingi masala</button>}
        </div>
      )}
      {isSelf && result?.needs_self_check && !("is_correct" in result && result.is_correct !== undefined && result.is_correct !== null) && (
        <div className="mp-feedback">
          <span>Yechimingiz quyidagiga mos keldimi?</span>
          <span style={{ display: "flex", gap: 8 }}>
            <button className="ui-btn" onClick={() => check(false)}>Yo'q</button>
            <button className="ui-btn primary" onClick={() => check(true)}>Ha, to'g'ri</button>
          </span>
        </div>
      )}

      <div className="mp-help">
        {problem.solution_steps?.length > 1 && !steps && (
          <button className="ui-btn sm" onClick={() => setHint(true)} disabled={hint}>Maslahat</button>
        )}
        {isSelf && !result
          ? <button className="ui-btn sm primary" onClick={() => check()}>Yechimni ko'rish</button>
          : <button className="ui-btn sm" onClick={() => setSteps(s => !s)}>{steps ? "Yechimni yashirish" : "Yechimni ko'rsatish"}</button>}
        <button className="ui-btn sm" onClick={explain} disabled={ai?.loading}>{ai?.loading ? "AI o'ylayapti..." : "AI tushuntirsin"}</button>
        {!correct && !wrong && <button className="ui-btn sm" onClick={onNext}>O'tkazib yuborish</button>}
      </div>

      {hint && !steps && problem.solution_steps?.[0] && (
        <div className="mp-hint"><b>Maslahat</b>Birinchi qadam: {pretty(problem.solution_steps[0])}</div>
      )}
      {steps && problem.solution_steps?.length > 0 && (
        <ol className="mp-steps">
          {problem.solution_steps.map((s, i) => <li key={i}>{pretty(s)}</li>)}
        </ol>
      )}
      {ai?.text && <div className="mp-ai"><b>AI Ustoz</b><RichText text={ai.text} /></div>}
    </article>
  );
}
