import React, { useEffect, useState } from "react";
import { fetchQuizList, publishQuiz, rebuildQuiz } from "../../api/client.js";
import { AdminPageHeader } from "./AdminLayout.jsx";

const LEVELS = ["", "A1", "A2", "B1", "B2", "C1", "C2"];

export default function AdminQuizzes() {
  const [level, setLevel] = useState("");
  const [onlyHidden, setOnlyHidden] = useState(false);
  const [rows, setRows] = useState(null);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(null);

  useEffect(() => {
    setRows(null);
    fetchQuizList({ level }).then(d => setRows(Array.isArray(d) ? d : d?.results || [])).catch(e => setMsg(e.message));
  }, [level]);

  async function toggle(q) {
    const r = await publishQuiz(q.id, !q.is_published).catch(e => { setMsg(e.message); return null; });
    if (r) setRows(list => list.map(x => (x.id === q.id ? { ...x, is_published: r.is_published } : x)));
  }
  async function rebuild(q) {
    setBusy(q.id); setMsg("");
    try {
      const r = await rebuildQuiz(q.id);
      setRows(list => list.map(x => (x.id === q.id ? { ...x, is_published: r.is_published } : x)));
      setMsg(`"${q.title}" qayta tuzildi.`);
    } catch (e) { setMsg(e.message); }
    setBusy(null);
  }

  const list = (rows || []).filter(q => !onlyHidden || !q.is_published);
  const hidden = (rows || []).filter(q => !q.is_published).length;

  return (
    <div>
      <AdminPageHeader title="Quizlar" subtitle="Daraja bo'yicha quizlar. Yashirin quizlar o'quvchilarga ko'rinmaydi." />
      <div className="adm-filter">
        {LEVELS.map(l => <button key={l} className={level === l ? "on" : ""} onClick={() => setLevel(l)}>{l || "Hammasi"}</button>)}
        <button className={onlyHidden ? "on" : ""} onClick={() => setOnlyHidden(v => !v)}>Faqat yashirin ({hidden})</button>
      </div>
      {msg && <div className="demo-banner" style={{ background: "oklch(0.96 0.03 275)" }}>{msg}</div>}
      <div className="admin-table">
        <div className="admin-table-head" style={{ gridTemplateColumns: "2fr 0.5fr 0.9fr 0.5fr 0.9fr 1.7fr" }}>
          <div>Nomi</div><div>Daraja</div><div>Turi</div><div>Savol</div><div>Holat</div><div></div>
        </div>
        {rows === null && <div className="admin-table-row"><div>Yuklanmoqda...</div></div>}
        {list.slice(0, 300).map(q => (
          <div key={q.id} className="admin-table-row" style={{ gridTemplateColumns: "2fr 0.5fr 0.9fr 0.5fr 0.9fr 1.7fr" }}>
            <div style={{ fontWeight: 600 }}>{q.title}</div>
            <div>{q.level || "—"}</div>
            <div>{{ grammar: "Grammatika", vocabulary: "So'zlar", other: "Boshqa" }[q.category]}</div>
            <div>{q.question_count}</div>
            <div><span className={"badge " + (q.is_published ? "on" : "off")}>{q.is_published ? "E'lon qilingan" : "Yashirin"}</span></div>
            <div style={{ display: "flex", gap: 6 }}>
              <button className="btn btn-outline" style={{ padding: "5px 10px", fontSize: 12.5, whiteSpace: "nowrap" }} onClick={() => toggle(q)}>{q.is_published ? "Yashirish" : "E'lon qilish"}</button>
              <button className="btn btn-outline" style={{ padding: "5px 10px", fontSize: 12.5, whiteSpace: "nowrap" }} onClick={() => rebuild(q)} disabled={busy === q.id}>{busy === q.id ? "..." : "Qayta tuzish (AI)"}</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
