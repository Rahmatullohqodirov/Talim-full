import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import {
  answerVocabularyWord, fetchVocabularyList, fetchVocabularySession, markVocabularyKnown,
} from "../api/client.js";
import "./app/ui.css";
import "./VocabularyLevel.css";

const LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"];
const POS_UZ = {
  noun: "ot", verb: "fe'l", adjective: "sifat", adverb: "ravish", preposition: "predlog", pronoun: "olmosh",
  determiner: "aniqlovchi", conjunction: "bog'lovchi", number: "son", interjection: "undov", "modal verb": "modal fe'l",
};

function speak(text, rate = 0.9) {
  if (!window.speechSynthesis || !text) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "en-US"; u.rate = rate;
  window.speechSynthesis.speak(u);
}
const shuffle = arr => { const a = [...arr]; for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };

export default function VocabularyLevel() {
  const { level: raw } = useParams();
  const [params, setParams] = useSearchParams();
  const level = String(raw || "").toUpperCase();
  const tab = params.get("mode") === "learn" ? "learn" : params.get("mode") === "list" ? "list" : "learn";

  if (!LEVELS.includes(level)) {
    return <div className="ui"><div className="ui-alert bad">Bunday daraja yo'q: "{raw}". <Link to="/app/vocabulary">Orqaga</Link></div></div>;
  }

  return (
    <div className="ui vl">
      <header className="ui-head">
        <div>
          <Link to="/app/vocabulary" className="vl-back">← So'z boyligi</Link>
          <h1>{level} so'zlari</h1>
        </div>
        <div className="ui-tabs" role="tablist">
          <button role="tab" aria-selected={tab === "learn"} className={tab === "learn" ? "on" : ""} onClick={() => setParams({ mode: "learn" })}>O'rganish</button>
          <button role="tab" aria-selected={tab === "list"} className={tab === "list" ? "on" : ""} onClick={() => setParams({ mode: "list" })}>Barcha so'zlar</button>
        </div>
      </header>
      {tab === "learn" ? <Learn level={level} /> : <WordList level={level} />}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* O'rganish: tanishuv -> mashq -> natija                              */
/* ------------------------------------------------------------------ */

function Learn({ level }) {
  const [words, setWords] = useState(null);
  const [phase, setPhase] = useState("intro"); // intro | practice | done
  const [i, setI] = useState(0);
  const [error, setError] = useState("");
  const [stats, setStats] = useState({ correct: 0, wrong: 0, points: 0, mastered: [] });
  const [known, setKnown] = useState(new Set());

  const load = useCallback(() => {
    setWords(null); setPhase("intro"); setI(0); setError(""); setKnown(new Set());
    setStats({ correct: 0, wrong: 0, points: 0, mastered: [] });
    fetchVocabularySession(level, 10)
      .then(d => setWords(d.words))
      .catch(e => setError(e.isNetworkError ? "Internet yo'q." : e.message || "So'zlarni yuklab bo'lmadi."));
  }, [level]);
  useEffect(load, [load]);

  const practiceWords = useMemo(() => (words || []).filter(w => !known.has(w.id)), [words, known]);
  const questions = useMemo(() => buildQuestions(practiceWords, words || []), [practiceWords, words]);

  if (error) return <div className="ui-alert bad">{error}</div>;
  if (!words) return <div className="ui-skeleton" style={{ height: 340 }} />;
  if (!words.length) return <div className="ui-card ui-empty"><strong>Bu darajadagi barcha so'zlar o'zlashtirilgan!</strong>Keyingi darajaga o'ting.</div>;

  if (phase === "intro") {
    const w = words[i];
    const isKnown = known.has(w.id);
    return (
      <div className="vl-learn">
        <Steps words={words} i={i} phase="intro" />
        <article className="ui-card vl-word" key={w.id}>
          <div className="vl-word-top">
            <span className="ui-badge">{POS_UZ[w.pos] || w.pos}</span>
            {w.status === "learning" && <span className="ui-badge pen">takrorlash</span>}
          </div>
          <h2 className="vl-head">{w.headword}
            <button className="vl-speak" onClick={() => speak(w.headword)} aria-label="Talaffuz"><SpeakerIcon /></button>
          </h2>
          <p className="vl-uz">{w.uz || <span className="ui-faint">Tarjima hali yo'q</span>}</p>
          {w.example && (
            <div className="vl-example">
              <p>{w.example} <button className="vl-speak sm" onClick={() => speak(w.example, 0.85)} aria-label="Misolni eshitish"><SpeakerIcon /></button></p>
              {w.example_uz && <p className="ui-faint">{w.example_uz}</p>}
            </div>
          )}
          <div className="vl-word-actions">
            <button className={"ui-btn" + (isKnown ? " ink" : "")} disabled={isKnown} onClick={() => {
              setKnown(new Set([...known, w.id]));
              markVocabularyKnown(w.id).catch(() => {});
            }}>{isKnown ? "Bilaman — mashqdan chiqarildi" : "Bu so'zni bilaman"}</button>
            <div style={{ flex: 1 }} />
            {i > 0 && <button className="ui-btn" onClick={() => setI(i - 1)}>Orqaga</button>}
            {i + 1 < words.length
              ? <button className="ui-btn primary" onClick={() => { setI(i + 1); speak(words[i + 1].headword); }}>Keyingi so'z</button>
              : <button className="ui-btn primary" onClick={() => { setI(0); setPhase(practiceWords.length ? "practice" : "done"); }}>Mashqqa o'tish</button>}
          </div>
        </article>
      </div>
    );
  }

  if (phase === "practice" && i < questions.length) {
    return (
      <div className="vl-learn">
        <Steps words={questions} i={i} phase="practice" />
        <Question key={`${questions[i].word.id}-${i}`} q={questions[i]}
          onAnswer={async correct => {
            try {
              const r = await answerVocabularyWord(questions[i].word.id, correct);
              setStats(s => ({
                correct: s.correct + (correct ? 1 : 0), wrong: s.wrong + (correct ? 0 : 1),
                points: s.points + (r.earned_points || 0),
                mastered: r.mastered && !s.mastered.includes(questions[i].word.headword) ? [...s.mastered, questions[i].word.headword] : s.mastered,
              }));
            } catch {
              setStats(s => ({ ...s, correct: s.correct + (correct ? 1 : 0), wrong: s.wrong + (correct ? 0 : 1) }));
            }
          }}
          onNext={() => (i + 1 < questions.length ? setI(i + 1) : setPhase("done"))}
        />
      </div>
    );
  }

  const total = stats.correct + stats.wrong;
  return (
    <div className="ui-card vl-done">
      <span className="vl-done-score">{total ? Math.round((stats.correct / total) * 100) : 100}%</span>
      <h2>Bugungi so'zlar tugadi</h2>
      <p className="ui-muted">{stats.correct} to'g'ri, {stats.wrong} xato{stats.points ? ` · +${stats.points} ball` : ""}{known.size ? ` · ${known.size} ta so'zni bilar ekansiz` : ""}</p>
      {stats.mastered.length > 0 && <p className="ui-muted">To'liq o'zlashtirildi: <strong>{stats.mastered.join(", ")}</strong></p>}
      <p className="ui-faint">Har bir so'z 4 marta to'g'ri topilganda o'zlashtirilgan hisoblanadi. Xato qilinganlari keyingi sessiyalarda yana chiqadi.</p>
      <div className="vl-done-actions">
        <Link to="/app/vocabulary" className="ui-btn">Darajalarga qaytish</Link>
        <button className="ui-btn primary" onClick={load}>Yana 10 ta so'z</button>
      </div>
    </div>
  );
}

function buildQuestions(practice, pool) {
  const withUz = pool.filter(w => w.uz);
  return shuffle(practice).map((word, n) => {
    const canTranslate = word.uz && withUz.length >= 4;
    const kind = !canTranslate ? "listen" : n % 3 === 1 ? "uz-en" : "en-uz";
    const others = shuffle((kind === "listen" ? pool : withUz).filter(w => w.id !== word.id));
    const label = w => (kind === "en-uz" ? w.uz : w.headword);
    const seen = new Set([label(word).toLowerCase()]);
    const distractors = [];
    for (const o of others) {
      const l = label(o).toLowerCase();
      if (!seen.has(l)) { seen.add(l); distractors.push(o); }
      if (distractors.length === 3) break;
    }
    return { word, kind, options: shuffle([word, ...distractors]) };
  });
}

function Question({ q, onAnswer, onNext }) {
  const [picked, setPicked] = useState(null);
  const { word, kind, options } = q;
  useEffect(() => { if (kind !== "uz-en") speak(word.headword); }, []); // eslint-disable-line

  function pick(o) {
    if (picked) return;
    setPicked(o.id);
    const ok = o.id === word.id;
    onAnswer(ok);
    if (ok && kind === "uz-en") speak(word.headword);
  }

  useEffect(() => {
    const onKey = e => {
      if (!picked && ["1", "2", "3", "4"].includes(e.key) && options[Number(e.key) - 1]) pick(options[Number(e.key) - 1]);
      if (picked && e.key === "Enter") onNext();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const prompt = kind === "en-uz" ? "Tarjimasini toping" : kind === "uz-en" ? "Inglizchasini toping" : "Eshiting va so'zni toping";
  return (
    <div className="ui-card vl-q">
      <p className="ui-faint">{prompt}</p>
      <h2 className="vl-q-word">
        {kind === "en-uz" && word.headword}
        {kind === "uz-en" && word.uz}
        {kind === "listen" && <button className="vl-listen" onClick={() => speak(word.headword, 0.8)} aria-label="Qayta eshitish"><SpeakerIcon size={34} /></button>}
        {kind === "en-uz" && <button className="vl-speak" onClick={() => speak(word.headword)} aria-label="Talaffuz"><SpeakerIcon /></button>}
      </h2>
      <div className="vl-options">
        {options.map((o, n) => {
          let cls = "vl-option";
          if (picked) cls += o.id === word.id ? " correct" : o.id === picked ? " wrong" : " dim";
          return (
            <button key={o.id} className={cls} onClick={() => pick(o)} disabled={!!picked}>
              <kbd>{n + 1}</kbd>{kind === "en-uz" ? o.uz : o.headword}
            </button>
          );
        })}
      </div>
      {picked && (
        <div className={"vl-feedback " + (picked === word.id ? "ok" : "bad")}>
          <span>{picked === word.id ? "To'g'ri!" : <><strong>{word.headword}</strong> — {word.uz || "…"}</>}</span>
          <button className="ui-btn primary" onClick={onNext} autoFocus>Keyingi</button>
        </div>
      )}
    </div>
  );
}

function Steps({ words, i, phase }) {
  return (
    <div className="vl-steps">
      <span className="ui-faint">{phase === "intro" ? "Tanishuv" : "Mashq"} · {i + 1}/{words.length}</span>
      <div className="vl-steps-bar">{words.map((_, n) => <i key={n} className={n < i ? "done" : n === i ? "now" : ""} />)}</div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Barcha so'zlar ro'yxati                                             */
/* ------------------------------------------------------------------ */

const STATUS_FILTERS = [
  { key: "", label: "Hammasi" },
  { key: "new", label: "Yangi" },
  { key: "learning", label: "O'rganilmoqda" },
  { key: "mastered", label: "O'zlashtirilgan" },
];

function WordList({ level }) {
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => { const t = setTimeout(() => { setQuery(search); setPage(1); }, 350); return () => clearTimeout(t); }, [search]);
  useEffect(() => {
    setData(null); setError("");
    fetchVocabularyList({ cefr: level, page, page_size: 30, search: query, status, translate: 1 })
      .then(setData)
      .catch(e => setError(e.message || "Yuklab bo'lmadi."));
  }, [level, page, query, status]);

  async function know(w) {
    try {
      const updated = await markVocabularyKnown(w.id);
      setData(d => ({ ...d, results: d.results.map(x => (x.id === w.id ? updated : x)) }));
    } catch { /* tarmoq xatosi */ }
  }

  return (
    <div className="vl-list">
      <div className="vl-list-tools">
        <input className="ui-input" placeholder="So'z yoki tarjima bo'yicha qidirish..." value={search} onChange={e => setSearch(e.target.value)} aria-label="Qidirish" />
        <div className="ui-chips">
          {STATUS_FILTERS.map(f => <button key={f.key} className={"ui-chip" + (status === f.key ? " on" : "")} onClick={() => { setStatus(f.key); setPage(1); }}>{f.label}</button>)}
        </div>
      </div>
      {error && <div className="ui-alert bad">{error}</div>}
      {!data && !error && <div className="ui-skeleton" style={{ height: 400 }} />}
      {data && (
        <>
          <p className="ui-faint">{data.total} ta so'z</p>
          <div className="ui-card vl-table">
            {data.results.length === 0 && <p className="ui-empty">Hech narsa topilmadi.</p>}
            {data.results.map(w => (
              <div key={w.id} className={"vl-row " + w.status}>
                <button className="vl-speak sm" onClick={() => speak(w.headword)} aria-label={`Talaffuz: ${w.headword}`}><SpeakerIcon /></button>
                <div className="vl-row-main">
                  <strong>{w.headword}</strong> <span className="ui-faint">{POS_UZ[w.pos] || w.pos}</span>
                  <div className="vl-row-uz">{w.uz || "—"}</div>
                </div>
                <div className="vl-row-mastery" title={`${w.mastery}%`}><i style={{ width: `${w.mastery}%` }} /></div>
                {w.status !== "mastered"
                  ? <button className="ui-btn sm" onClick={() => know(w)}>Bilaman</button>
                  : <span className="ui-badge ok">O'zlashtirilgan</span>}
              </div>
            ))}
          </div>
          {data.pages > 1 && (
            <div className="vl-pager">
              <button className="ui-btn sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Oldingi</button>
              <span className="ui-faint">{page} / {data.pages}</span>
              <button className="ui-btn sm" disabled={page >= data.pages} onClick={() => setPage(p => p + 1)}>Keyingi</button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function SpeakerIcon({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M11 5 6 9H2v6h4l5 4V5Z" /><path d="M15.5 8.5a5 5 0 0 1 0 7M19 5a10 10 0 0 1 0 14" />
    </svg>
  );
}
