import React, { useEffect, useState } from "react";
import { fetchAdminStories, updateAdminStory, deleteAdminStory, generateAdminStories } from "../../api/client.js";
import { AdminPageHeader, AddModal, useModal, RowActions } from "./AdminLayout.jsx";

const LEVELS = ["A1", "A2", "B1", "B2"];
const COLORS = ["violet", "amber", "teal", "rose", "sky", "lime"];

const FIELDS = [
  { name: "title", label: "Hikoya nomi", placeholder: "Masalan: My Day" },
  { name: "text", label: "Matn", type: "textarea", rows: 6, placeholder: "Hikoya matni (inglizcha)..." },
  { name: "cover_emoji", label: "Muqova emoji", placeholder: "🌅" },
  { name: "cover_color", label: "Muqova rangi", type: "select", options: COLORS.map(c => ({ value: c, label: c })) },
  { name: "order", label: "Tartib raqami", type: "number", placeholder: "1" },
  { name: "is_published", label: "E'lon qilingan (o'quvchilarga ko'rinadi)", type: "checkbox" },
];

export default function AdminStories() {
  const [genLevel, setGenLevel] = useState("A1");
  const [rows, setRows] = useState(null);
  const [msg, setMsg] = useState("");
  const [genBusy, setGenBusy] = useState(false);
  const modal = useModal();

  function load() {
    setRows(null);
    fetchAdminStories().then(d => setRows(Array.isArray(d) ? d : d?.results || [])).catch(e => setMsg(e.message));
  }

  useEffect(load, []);

  async function handleSave(values) {
    await updateAdminStory(modal.editItem.id, { ...values, order: Number(values.order) || 0 });
    load();
  }

  async function handleDelete(s) {
    await deleteAdminStory(s.id).catch(e => setMsg(e.message));
    load();
  }

  async function handleGenerate() {
    setGenBusy(true); setMsg("");
    try {
      const r = await generateAdminStories("english", genLevel);
      setMsg(`AI ${r.created} ta yangi hikoya yaratdi (${genLevel}).`);
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
        title="Tinglang va o'qing"
        subtitle="Qisqa hikoyalar kutubxonasi — audio, tushunish savollari bilan. Yangi hikoyalarni AI yordamida avtomatik yarating."
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
        <div className="admin-table-head" style={{ gridTemplateColumns: "0.6fr 0.6fr 1.8fr 0.8fr 0.9fr 1fr" }}>
          <div>Tartib</div><div>Muqova</div><div>Nomi</div><div>Savol</div><div>Holat</div><div></div>
        </div>
        {rows === null && <div className="admin-table-row"><div>Yuklanmoqda...</div></div>}
        {rows?.length === 0 && <div className="admin-table-row"><div>Hozircha hikoya yo'q. AI bilan yarating.</div></div>}
        {sorted.map(s => (
          <div key={s.id} className="admin-table-row" style={{ gridTemplateColumns: "0.6fr 0.6fr 1.8fr 0.8fr 0.9fr 1fr" }}>
            <div>{s.order}</div>
            <div style={{ fontSize: 18 }}>{s.cover_emoji}</div>
            <div style={{ fontWeight: 600 }}>{s.title}</div>
            <div>{s.questions?.length ?? 0}</div>
            <div><span className={"badge " + (s.is_published ? "on" : "off")}>{s.is_published ? "E'lon qilingan" : "Yashirin"}</span></div>
            <RowActions onEdit={() => modal.openEdit(s)} onDelete={() => handleDelete(s)} deleteLabel={`"${s.title}" hikoyasini o'chirishni tasdiqlaysizmi?`} />
          </div>
        ))}
      </div>

      {modal.open && modal.editItem && (
        <AddModal
          title="Hikoyani tahrirlash"
          fields={FIELDS}
          initialValues={modal.editItem}
          onSubmit={handleSave}
          onClose={modal.closeModal}
        />
      )}
    </div>
  );
}
