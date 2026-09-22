import React, { useEffect, useState } from "react";
import { fetchLeaderboard } from "../../api/client.js";
import "./Leaderboard.css";

export default function Leaderboard() {
  const [rows, setRows] = useState([]);
  const [scope, setScope] = useState("global_anon");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    fetchLeaderboard(scope)
      .then(data => {
        if (!cancelled) setRows(Array.isArray(data) ? data : (data?.results || []));
      })
      .catch(err => { if (!cancelled) setError(err.message || "Leaderboard yuklanmadi."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [scope]);

  return (
    <div>
      <h1 className="page-title" style={{ marginBottom: 10 }}>Leaderboard</h1>
      <p className="page-sub">Haftalik natijalarda o'quvchilar reytingi</p>

      <div className="tab-row" style={{ marginBottom: 20 }}>
        <button className={"tab-btn" + (scope === "global_anon" ? " active" : "")} onClick={() => setScope("global_anon")}>Global</button>
        <button className={"tab-btn" + (scope === "friends" ? " active" : "")} onClick={() => setScope("friends")}>Do'stlar</button>
      </div>

      {loading && <div className="page-sub">Yuklanmoqda...</div>}
      {error && <div className="math-feedback wrong">{error}</div>}
      {!loading && !error && !rows.length && <div className="page-sub">Hozircha reyting ma'lumotlari yo'q.</div>}

      <div className="lb-list">
        {rows.map((row, i) => (
          <div key={`${row.username}-${row.rank ?? i}`} className="lb-row">
            <div className="lb-rank">#{row.rank ?? i + 1}</div>
            <div className="lb-name">{row.username}</div>
            <div className="lb-points">{row.total_points ?? 0} ball</div>
          </div>
        ))}
      </div>
    </div>
  );
}
