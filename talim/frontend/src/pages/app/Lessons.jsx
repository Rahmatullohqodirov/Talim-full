import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { fetchLessons, fetchStories } from "../../api/client.js";
import "./ui.css";
import "./Lessons.css";

const TABS = [
  { key: "lessons", label: "Darslar" },
  { key: "stories", label: "Tinglang va o'qing" },
];

export default function Lessons() {
  const [params, setParams] = useSearchParams();
  const tab = TABS.some(t => t.key === params.get("tab")) ? params.get("tab") : "lessons";
  const navigate = useNavigate();
  const [lessons, setLessons] = useState(null);
  const [stories, setStories] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchLessons("english", "A1").then(setLessons).catch(e => setError(e.message || "Yuklab bo'lmadi."));
    fetchStories("english", "A1").then(setStories).catch(() => {});
  }, []);

  return (
    <div className="ui lsn">
      <header className="ui-head">
        <div>
          <h1>Darslar</h1>
          <p>Grammatika darsi — so'zlar lug'ati va mashqlar bilan — hamda tinglab-o'qish uchun qisqa hikoyalar.</p>
        </div>
        <nav className="ui-tabs" role="tablist">
          {TABS.map(t => (
            <button key={t.key} role="tab" aria-selected={tab === t.key} className={tab === t.key ? "on" : ""}
              onClick={() => setParams(t.key === "lessons" ? {} : { tab: t.key })}>
              {t.label}
            </button>
          ))}
        </nav>
      </header>

      {error && <div className="ui-alert bad">{error}</div>}

      {tab === "lessons" ? (
        <div className="lsn-grid">
          {lessons === null && !error && [0, 1, 2, 3].map(i => <div key={i} className="ui-skeleton" style={{ height: 120 }} />)}
          {lessons?.map((l, i) => (
            <button key={l.id} className={"ui-card lsn-card" + (l.completed ? " done" : "")}
              onClick={() => navigate(`/app/lessons/${l.id}`)}>
              <span className="lsn-num">{i + 1}-dars</span>
              <h2>{l.title}</h2>
              <div className="lsn-card-meta">
                <span className="ui-faint">{l.word_count} so'z · {l.exercise_count} mashq</span>
                {l.completed
                  ? <span className="ui-badge ok">✓ {l.score?.correct}/{l.score?.total}</span>
                  : <span className="ui-badge">Boshlanmagan</span>}
              </div>
            </button>
          ))}
          {lessons?.length === 0 && (
            <div className="ui-empty"><strong>Hozircha dars yo'q</strong>Tez orada qo'shiladi.</div>
          )}
        </div>
      ) : (
        <div className="lsn-grid stories">
          {stories === null && !error && [0, 1, 2, 3].map(i => <div key={i} className="ui-skeleton" style={{ height: 150 }} />)}
          {stories?.map(s => (
            <button key={s.id} className={`ui-card lsn-story ${s.cover_color}`} onClick={() => navigate(`/app/stories/${s.id}`)}>
              <span className="lsn-story-cover">{s.cover_emoji}</span>
              <h2>{s.title}</h2>
              <div className="lsn-card-meta">
                <span className="ui-badge accent">{s.level}</span>
                {s.my_result
                  ? <span className="ui-faint">Natija: {s.my_result.correct} / {s.my_result.total}</span>
                  : <span className="ui-faint">{s.question_count} ta savol</span>}
              </div>
            </button>
          ))}
          {stories?.length === 0 && (
            <div className="ui-empty"><strong>Hozircha hikoya yo'q</strong>Tez orada qo'shiladi.</div>
          )}
        </div>
      )}
    </div>
  );
}
