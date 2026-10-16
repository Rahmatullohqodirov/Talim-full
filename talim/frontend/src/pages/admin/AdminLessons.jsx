import React, { useEffect, useState } from "react";
import { fetchAdminLessons, updateAdminLesson, deleteAdminLesson, generateAdminLessons } from "../../api/client.js";
import { AdminPageHeader, AddModal, useModal, RowActions } from "./AdminLayout.jsx";

const LEVELS = ["A1", "A2", "B1", "B2"];

const FIELDS = [
  { name: "title", label: "Dars nomi", placeholder: "Masalan: Fe'lning asosiy shakli (to be)" },
  { name: "explanation", label: "Qoida tushuntirishi", type: "textarea", rows: 4, placeholder: "Qisqa grammatika tushuntirishi..." },
  { name: "order", label: "Tartib raqami", type: "number", placeholder: "1" },
  { name: "is_published", label: "E'lon qilingan (o'quvchilarga ko'rinadi)", type: "checkbox" },
];

export default function AdminLessons() {
  const [genLevel, setGenLevel] = useState("A1");
  const [rows, setRows] = useState(null);
  const [msg, setMsg] = useState("");
  const [genBusy, setGenBusy] = useState(false);
  const modal = useModal();

  function load() {
    setRows(null);
    fetchAdminLessons().then(d => setRows(Array.isArray(d) ? d : d?.results || [])).catch(e => setMsg(e.message));
  }

  useEffect(load, []);

  async function handleSave(values) {
    await updateAdminLesson(modal.editItem.id, { ...values, order: Number(values.order) || 0 });
    load();
  }

  async function handleDelete(l) {
    await deleteAdminLesson(l.id).catch(e => setMsg(e.message));
    load();
  }

  async function handleGenerate() {
    setGenBusy(true); setMsg("");
    try {
      const r = await generateAdminLessons("english", genLevel);
      setMsg(`AI ${r.created} ta yangi dars yaratdi (${genLevel}).`);
      load();
    } catch (e) {
      setMsg(e.message || "AI generatsiya qilib bo'lmadi.");
    }
    setGenBusy(false);
  }

  const sorted = [...(rows || [])].sort((a, b) => (a.order ?? 0) - (b.order ?? 0));

  return (
    <div>
      <AdminPageHeader
        title="Darslar"
        subtitle="Grammatika darslari — so'zlar lug'ati va mashqlar bilan. Yangi darslarni AI yordamida avtomatik yarating."
        action={
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <select className="input" style={{ width: 90 }} value={genLevel} onChange={e => setGenLevel(e.target.value)}>
              {LEVELS.map(l => <option key={l} value={l}>{l}</option>)}
            </select>
            <button className="btn btn-primary" onClick={handleGenerate} disabled={genBusy}>
              {genBusy ? "Yaratilmoqda..." : "✦ AI bilan yaratish"}
            </button>
          </div>
        }
      />
      {msg && <div className="demo-banner" style={{ background: "oklch(0.96 0.03 275)" }}>{msg}</div>}
      <div className="admin-table">
        <div className="admin-table-head" style={{ gridTemplateColumns: "0.6fr 2.2fr 0.7fr 0.7fr 0.9fr 1fr" }}>
          <div>Tartib</div><div>Nomi</div><div>So'z</div><div>Mashq</div><div>Holat</div><div></div>
        </div>
        {rows === null && <div className="admin-table-row"><div>Yuklanmoqda...</div></div>}
        {rows?.length === 0 && <div className="admin-table-row"><div>Hozircha dars yo'q. AI bilan yarating.</div></div>}
        {sorted.map(l => (
          <div key={l.id} className="admin-table-row" style={{ gridTemplateColumns: "0.6fr 2.2fr 0.7fr 0.7fr 0.9fr 1fr" }}>
            <div>{l.order}</div>
            <div style={{ fontWeight: 600 }}>{l.title}</div>
            <div>{l.words?.length ?? 0}</div>
            <div>{l.exercises?.length ?? 0}</div>
            <div><span className={"badge " + (l.is_published ? "on" : "off")}>{l.is_published ? "E'lon qilingan" : "Yashirin"}</span></div>
            <RowActions onEdit={() => modal.openEdit(l)} onDelete={() => handleDelete(l)} deleteLabel={`"${l.title}" darsini o'chirishni tasdiqlaysizmi?`} />
          </div>
        ))}
      </div>

      {modal.open && modal.editItem && (
        <AddModal
          title="Darsni tahrirlash"
          fields={FIELDS}
          initialValues={modal.editItem}
          onSubmit={handleSave}
          onClose={modal.closeModal}
        />
      )}
    </div>
  );
}
