import React, { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchLesson, submitLesson } from "../../api/client.js";
import "./ui.css";
import "./LessonDetail.css";

const KIND_LABEL = {
  words: "So'zlar lug'ati",
  en_uz: "Inglizcha → O'zbekcha",
  uz_en: "O'zbekcha → Inglizcha",
  fill_blank: "Tushib qolgan so'zni topish",
  build_sentence: "Matn tuzish",
};
const SUB_TABS = ["words", "en_uz", "uz_en", "fill_blank", "build_sentence"];

export default function LessonDetail() {
  const { id } = useParams();
  const [lesson, setLesson] = useState(null);
  const [error, setError] = useState("");
  const [sub, setSub] = useState("words");
  const [answers, setAnswers] = useState({});   // exercise_id -> matnli javob
  const [picks, setPicks] = useState({});       // build_sentence: exercise_id -> tanlangan so'zlar ro'yxati
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetchLesson(id).then(setLesson).catch(e => setError(e.message || "Yuklab bo'lmadi."));
  }, [id]);

  const byKind = useMemo(() => {
    const g = { en_uz: [], uz_en: [], fill_blank: [], build_sentence: [] };
    (lesson?.exercises || []).forEach(e => { g[e.kind]?.push(e); });
    return g;
  }, [lesson]);

  function setAnswer(exId, value) {
    setAnswers(a => ({ ...a, [exId]: value }));
  }

  function toggleWord(exId, bank, word) {
    setPicks(p => {
      const cur = p[exId] || [];
      const next = cur.includes(word) ? cur.filter(w => w !== word) : [...cur, word];
      setAnswer(exId, next.join(" "));
      return { ...p, [exId]: next };
    });
  }

  async function finish() {
    setBusy(true); setError("");
    try {
      const r = await submitLesson(id, answers);
      setResult(r);
    } catch (e) {
      setError(e.message || "Yuborib bo'lmadi.");
    } finally {
      setBusy(false);
    }
  }

  function retry() {
    setResult(null); setAnswers({}); setPicks({});
  }

  if (error && !lesson) return <div className="ui"><div className="ui-alert bad">{error}</div></div>;
  if (!lesson) return <div className="ui lsnd"><div className="ui-skeleton" style={{ height: 260 }} /></div>;

  const answeredState = id2 => {
    if (!result) return null;
    const correctAnswer = result.answers?.[id2];
    if (correctAnswer === undefined) return null;
    const given = (answers[id2] || "").trim().toLowerCase();
    return given === String(correctAnswer).trim().toLowerCase() ? "ok" : "bad";
  };

  return (
    <div className="ui lsnd">
      <header className="ui-head">
        <div>
          <Link to="/app/lessons" className="lsnd-back">← Darslar</Link>
          <h1>{lesson.title}</h1>
          {lesson.explanation && <p>{lesson.explanation}</p>}
        </div>
        {result && (
          <div className={"ui-badge " + (result.completed ? "ok" : "")} style={{ fontSize: 14, padding: "6px 14px" }}>
            Natija: {result.correct} / {result.total} {result.points > 0 && `· +${result.points} ball`}
          </div>
        )}
      </header>

      <nav className="ui-tabs lsnd-tabs" role="tablist">
        {SUB_TABS.map(k => (
          <button key={k} role="tab" aria-selected={sub === k} className={sub === k ? "on" : ""} onClick={() => setSub(k)}>
            {KIND_LABEL[k]}
            {k !== "words" && <span className="lsnd-count">{byKind[k]?.length || 0}</span>}
          </button>
        ))}
      </nav>

      {error && <div className="ui-alert bad">{error}</div>}

      {sub === "words" && (
        <ul className="ui-card lsnd-words">
          {lesson.words.map(w => (
            <li key={w.id}><span>{w.word}</span><span className="ui-faint">{w.translation}</span></li>
          ))}
        </ul>
      )}

      {(sub === "en_uz" || sub === "uz_en") && (
        <div className="lsnd-exlist">
          {byKind[sub].map(e => (
            <div key={e.id} className={"ui-card lsnd-ex " + (answeredState(e.id) || "")}>
              <p className="lsnd-ex-prompt">{e.prompt}</p>
              <input className="ui-input" value={answers[e.id] || ""} onChange={ev => setAnswer(e.id, ev.target.value)}
                placeholder="Tarjimasini yozing" disabled={!!result} />
              {answeredState(e.id) === "bad" && <p className="lsnd-ex-correct">To'g'ri: {result.answers[e.id]}</p>}
            </div>
          ))}
        </div>
      )}

      {sub === "fill_blank" && (
        <div className="lsnd-exlist">
          {byKind.fill_blank.map(e => (
            <div key={e.id} className={"ui-card lsnd-ex " + (answeredState(e.id) || "")}>
              <p className="lsnd-ex-prompt">{e.prompt}</p>
              <div className="ui-chips">
                {e.bank.map(w => (
                  <button key={w} type="button" className={"ui-chip" + (answers[e.id] === w ? " on" : "")}
                    disabled={!!result} onClick={() => setAnswer(e.id, w)}>{w}</button>
                ))}
              </div>
              {answeredState(e.id) === "bad" && <p className="lsnd-ex-correct">To'g'ri: {result.answers[e.id]}</p>}
            </div>
          ))}
        </div>
      )}

      {sub === "build_sentence" && (
        <div className="lsnd-exlist">
          {byKind.build_sentence.map(e => (
            <div key={e.id} className={"ui-card lsnd-ex " + (answeredState(e.id) || "")}>
              <p className="lsnd-ex-prompt">Gapni to'g'ri tartibda tuzing:</p>
              <p className="lsnd-built">{picks[e.id]?.join(" ") || <span className="ui-faint">so'zlarni tanlang</span>}</p>
              <div className="ui-chips">
                {e.bank.map((w, i) => (
                  <button key={w + i} type="button" className={"ui-chip" + ((picks[e.id] || []).includes(w) ? " on" : "")}
                    disabled={!!result} onClick={() => toggleWord(e.id, e.bank, w)}>{w}</button>
                ))}
              </div>
              {answeredState(e.id) === "bad" && <p className="lsnd-ex-correct">To'g'ri: {result.answers[e.id]}</p>}
            </div>
          ))}
        </div>
      )}

      <div className="lsnd-foot">
        {!result ? (
          <button className="ui-btn primary" onClick={finish} disabled={busy}>
            {busy ? "Tekshirilmoqda..." : "Natijani ko'rish"}
          </button>
        ) : (
          <button className="ui-btn" onClick={retry}>Qayta urinish</button>
        )}
      </div>
    </div>
  );
}
