import React, { useEffect, useState } from "react";
import { fetchLeaderboardPeriod } from "../../api/client.js";
import { AdminPageHeader } from "./AdminLayout.jsx";

export default function AdminLeaderboard() {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");
  useEffect(() => {
    fetchLeaderboardPeriod("week")
      .then(data => setRows(Array.isArray(data) ? data : (data?.entries || data?.results || [])))
      .catch(e => setError(e.message || "Leaderboard yuklanmadi."));
  }, []);
  return <div>
    <AdminPageHeader title="Leaderboard" subtitle="Global haftalik reytingni ko'rish" />
    {error && <div className="math-feedback wrong">{error}</div>}
    <div className="admin-table">
      <div className="admin-table-head" style={{ gridTemplateColumns: ".5fr 2fr 1fr 1fr" }}>
        <div>#</div><div>Foydalanuvchi</div><div>Ball (hafta)</div><div>Daraja</div>
      </div>
      {rows.map((r, i) => <div className="admin-table-row" key={`${r.username}-${r.rank ?? i}`}>
        <div>#{r.rank ?? i + 1}</div><div>{r.username}</div><div>{r.total_points ?? 0}</div><div>{r.level || "—"}</div>
      </div>)}
    </div>
  </div>;
}
