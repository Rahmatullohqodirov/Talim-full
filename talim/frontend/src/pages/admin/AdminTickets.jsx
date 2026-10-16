import React, { useEffect, useState } from "react";
import { fetchAdminTickets, updateAdminTicket } from "../../api/client.js";
import { AdminPageHeader } from "./AdminLayout.jsx";

const STATUSES = [
  { key: "open", label: "Ochiq" },
  { key: "in_progress", label: "Ko'rib chiqilmoqda" },
  { key: "resolved", label: "Hal qilindi" },
];

export default function AdminTickets() {
  const [filter, setFilter] = useState("open");
  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setRows(null);
    fetchAdminTickets(filter).then(d => setRows(Array.isArray(d) ? d : d?.results || [])).catch(e => setError(e.message));
  }, [filter]);

  async function setStatus(t, status) {
    try {
      await updateAdminTicket(t.id, { status });
      setRows(list => list.filter(x => x.id !== t.id || status === filter).map(x => (x.id === t.id ? { ...x, status } : x)));
    } catch (e) { setError(e.message); }
  }

  return (
    <div>
      <AdminPageHeader title="Murojaatlar" subtitle="AI Ustoz hal qila olmagan masalalar: to'lov, texnik nosozlik, shikoyat" />
      <div className="adm-filter">
        {[...STATUSES, { key: "", label: "Hammasi" }].map(s => (
          <button key={s.key} className={filter === s.key ? "on" : ""} onClick={() => setFilter(s.key)}>{s.label}</button>
        ))}
      </div>
      {error && <div className="math-feedback wrong">{error}</div>}
      <div className="admin-table">
        <div className="admin-table-head" style={{ gridTemplateColumns: "1.2fr 0.8fr 2.6fr 0.9fr 1fr" }}>
          <div>Foydalanuvchi</div><div>Turi</div><div>Muammo</div><div>Sana</div><div>Holat</div>
        </div>
        {rows === null && <div className="admin-table-row"><div>Yuklanmoqda...</div></div>}
        {rows?.length === 0 && <div className="admin-table-row"><div style={{ color: "var(--text-muted)" }}>Murojaat yo'q.</div></div>}
        {rows?.map(t => (
          <div key={t.id} className="admin-table-row" style={{ gridTemplateColumns: "1.2fr 0.8fr 2.6fr 0.9fr 1fr" }}>
            <div><b>{t.username}</b><div style={{ fontSize: 12, color: "var(--text-muted)" }}>{t.email}</div></div>
            <div><span className={"badge " + (t.category === "payment" ? "on" : "off")}>{t.category_label}</span></div>
            <div className="adm-reason">{t.reason}</div>
            <div style={{ fontSize: 12.5 }}>{new Date(t.created_at).toLocaleString("ru-RU")}</div>
            <div>
              <select className="adm-select" value={t.status} onChange={e => setStatus(t, e.target.value)} aria-label="Holat">
                {STATUSES.map(s => <option key={s.key} value={s.key}>{s.label}</option>)}
              </select>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
