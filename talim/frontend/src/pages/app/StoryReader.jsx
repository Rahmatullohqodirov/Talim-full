import React, { useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchStory, submitStory } from "../../api/client.js";
import "./ui.css";
import "./StoryReader.css";

const SPEEDS = [
  { key: "slow", label: "Sekin", rate: 0.65 },
  { key: "normal", label: "Oddiy", rate: 1 },
  { key: "fast", label: "Tez", rate: 1.3 },
];

export default function StoryReader() {
  const { id } = useParams();
  const [story, setStory] = useState(null);
  const [error, setError] = useState("");
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [speed, setSpeed] = useState("normal");
  const [playing, setPlaying] = useState(false);
  const [copied, setCopied] = useState(false);
  const utterRef = useRef(null);

  useEffect(() => {
    fetchStory(id).then(setStory).catch(e => setError(e.message || "Yuklab bo'lmadi."));
    return () => { window.speechSynthesis?.cancel(); };
  }, [id]);

  const answeredCount = useMemo(() => Object.keys(answers).length, [answers]);

  function pick(qId, option) {
    if (result) return;
    setAnswers(a => ({ ...a, [qId]: option }));
  }

  function play() {
    if (!story?.text || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(story.text);
    u.lang = "en-US";
    u.rate = SPEEDS.find(s => s.key === speed)?.rate || 1;
    u.onend = () => setPlaying(false);
    u.onerror = () => setPlaying(false);
    utterRef.current = u;
    window.speechSynthesis.speak(u);
    setPlaying(true);
  }

  function stop() {
    window.speechSynthesis?.cancel();
    setPlaying(false);
  }

  async function copyStory() {
    try {
      await navigator.clipboard.writeText(story.text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      setError("Nusxalab bo'lmadi.");
    }
  }

  async function finish() {
    setBusy(true); setError("");
    try {
      const r = await submitStory(id, answers);
      setResult(r);
    } catch (e) {
      setError(e.message || "Yuborib bo'lmadi.");
    } finally {
      setBusy(false);
    }
  }

  function retry() {
    setResult(null); setAnswers({});
  }

  if (error && !story) return <div className="ui"><div className="ui-alert bad">{error}</div></div>;
  if (!story) return <div className="ui strd"><div className="ui-skeleton" style={{ height: 300 }} /></div>;

  const correctFor = qId => result?.answers?.[qId];

  return (
    <div className="ui strd">
      <header className="ui-head">
        <div>
          <Link to="/app/lessons?tab=stories" className="lsnd-back">← Tinglang va o'qing</Link>
          <h1>{story.cover_emoji} {story.title}</h1>
        </div>
        {result && (
          <div className={"ui-badge " + (result.completed ? "ok" : "")} style={{ fontSize: 14, padding: "6px 14px" }}>
            Natija: {result.correct} / {result.total} {result.points > 0 && `· +${result.points} ball`}
          </div>
        )}
      </header>

      {error && <div className="ui-alert bad">{error}</div>}

      <div className={`ui-card strd-cover ${story.cover_color}`}>
        <span className="strd-cover-emoji">{story.cover_emoji}</span>
        <span className="ui-badge accent">{story.level}</span>
      </div>

      <div className="ui-card strd-text">
        <p>{story.text}</p>
        <div className="strd-tools">
          <button className="ui-btn" onClick={copyStory}>{copied ? "Nusxalandi ✓" : "Nusxalash"}</button>
          <div className="strd-audio">
            <div className="ui-chips">
              {SPEEDS.map(s => (
                <button key={s.key} type="button" className={"ui-chip" + (speed === s.key ? " on" : "")}
                  onClick={() => setSpeed(s.key)}>{s.label}</button>
              ))}
            </div>
            {!playing ? (
              <button className="ui-btn primary" onClick={play}>▶ Tinglash</button>
            ) : (
              <button className="ui-btn" onClick={stop}>■ To'xtatish</button>
            )}
          </div>
        </div>
      </div>

      {story.questions?.length > 0 && (
        <div className="strd-questions">
          <h2>Matn bo'yicha savollar</h2>
          {story.questions.map(q => (
            <div key={q.id} className={"ui-card strd-q " + (result ? (answers[q.id] === correctFor(q.id) ? "ok" : "bad") : "")}>
              <p className="strd-q-text">{q.question}</p>
              <div className="strd-options">
                {q.options.map(opt => (
                  <button key={opt} type="button" disabled={!!result}
                    className={"strd-opt" + (answers[q.id] === opt ? " on" : "") + (result && opt === correctFor(q.id) ? " correct" : "")}
                    onClick={() => pick(q.id, opt)}>
                    {opt}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="lsnd-foot">
        {!result ? (
          <button className="ui-btn primary" onClick={finish} disabled={busy || answeredCount === 0}>
            {busy ? "Tekshirilmoqda..." : "Natijani ko'rish"}
          </button>
        ) : (
          <button className="ui-btn" onClick={retry}>Qayta urinish</button>
        )}
      </div>
    </div>
  );
}
