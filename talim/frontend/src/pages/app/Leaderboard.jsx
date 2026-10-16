import React, { useEffect, useState } from "react";
import { fetchLeaderboardPeriod } from "../../api/client.js";
import "./ui.css";
import "./Leaderboard.css";

const PERIODS = [
  { key: "week", label: "Shu hafta" },
  { key: "month", label: "Shu oy" },
  { key: "all", label: "Barcha vaqt" },
];

const initials = name => name.split(/\s+/).map(w => w[0]).join("").slice(0, 2).toUpperCase();

export default function Leaderboard() {
  const [period, setPeriod] = useState("week");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setData(null);
    setError("");
    fetchLeaderboardPeriod(period)
      .then(d => { if (!cancelled) setData(d); })
      .catch(e => { if (!cancelled) setError(e.message || "Reytingni yuklab bo'lmadi."); });
    return () => { cancelled = true; };
  }, [period]);

  const entries = data?.entries || [];
  const podium = entries.slice(0, 3);
  const rest = entries.slice(3);
  const meInTop = entries.some(e => e.is_me);

  return (
    <div className="ui lb">
      <header className="ui-head">
        <div>
          <h1>Reyting</h1>
          <p>Eng faol 50 o'quvchi. Ball quiz, flashcard, so'z o'rganish, AI Ustoz darslari va reja vazifalari uchun beriladi.</p>
        </div>
        <div className="ui-tabs" role="tablist">
          {PERIODS.map(p => (
            <button key={p.key} role="tab" aria-selected={period === p.key}
              className={period === p.key ? "on" : ""} onClick={() => setPeriod(p.key)}>{p.label}</button>
          ))}
        </div>
      </header>

      {error && <div className="ui-alert bad">{error}</div>}
      {!data && !error && <div className="ui-skeleton" style={{ height: 320 }} />}

      {data && !entries.length && (
        <div className="ui-card ui-empty">
          <strong>{period === "week" ? "Bu hafta hali hech kim ball to'plamadi" : "Hali reyting yo'q"}</strong>
          Birinchi bo'ling: quiz yeching yoki flashcardlarni takrorlang.
        </div>
      )}

      {podium.length > 0 && (
        <ol className="lb-podium" aria-label="Birinchi uch o'rin">
          {[[podium[1], 2], [podium[0], 1], [podium[2], 3]].filter(([e]) => e).map(([e, pos]) => (
            <li key={e.username} className={`lb-pod lb-pod-${pos}` + (e.is_me ? " me" : "")}>
              <span className="lb-avatar">{initials(e.name)}</span>
              <span className="lb-pod-name">{e.name}{e.is_me && " (siz)"}</span>
              <span className="lb-pod-points">{e.points} ball</span>
              <span className="lb-pod-stand"><b>{e.rank}</b></span>
            </li>
          ))}
        </ol>
      )}

      {rest.length > 0 && (
        <div className="ui-card lb-table">
          <ol>
            {rest.map(e => (
              <li key={e.username} className={e.is_me ? "me" : ""}>
                <span className="lb-rank">{e.rank}</span>
                <span className="lb-avatar sm">{initials(e.name)}</span>
                <span className="lb-name">{e.name}{e.is_me && <span className="ui-badge accent">siz</span>}</span>
                <span className="lb-meta">
                  {e.level && <span className="ui-badge">{e.level}</span>}
                  {e.streak > 0 && <span className="lb-streak" title="Kunlik seriya">{e.streak} kun</span>}
                </span>
                <span className="lb-points">{e.points}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {data && !meInTop && (
        <div className="lb-me-bar">
          {data.me
            ? <>Siz <strong>{data.me.rank}-o'rindasiz</strong> · {data.me.points} ball. Top 50 ga kirish uchun mashq qilishda davom eting.</>
            : <>Bu davrda hali ball yo'q. Bitta quiz yoki 10 ta flashcard bilan reytingga kiring.</>}
          <span className="ui-faint">{data.participants} ishtirokchi</span>
        </div>
      )}
    </div>
  );
}
