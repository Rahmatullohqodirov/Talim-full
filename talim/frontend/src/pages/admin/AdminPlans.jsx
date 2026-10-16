import React, { useEffect, useState } from "react";
import { createAdminPlan, deleteAdminPlan, fetchAdminPlans, updateAdminPlan } from "../../api/client.js";
import { AddModal, AdminPageHeader, RowActions, useModal } from "./AdminLayout.jsx";

const FIELDS = [
  { name: "name", label: "Nomi", placeholder: "Premium" },
  { name: "price_usd", label: "Narxi (USD)", type: "number", help: "To'lovda so'mga USD_TO_UZS_RATE kursi bo'yicha aylantiriladi." },
  { name: "duration_days", label: "Muddati (kun)", type: "number" },
  { name: "features", label: "Imkoniyatlar", type: "textarea", rows: 5, help: "Har biri alohida qatorda. Obuna sahifasida shu ro'yxat ko'rinadi." },
  { name: "max_sessions_per_day", label: "Kuniga avatar suhbatlari (ixtiyoriy)", type: "number" },
  { name: "voice_cloning_enabled", label: "Ovozni klonlash", type: "checkbox" },
  { name: "is_active", label: "Sotuvda", type: "checkbox" },
];

const toPayload = v => ({
  name: v.name, price_usd: v.price_usd, duration_days: Number(v.duration_days || 30),
  features: String(v.features || "").split("\n").map(x => x.trim()).filter(Boolean),
  max_sessions_per_day: v.max_sessions_per_day ? Number(v.max_sessions_per_day) : null,
  voice_cloning_enabled: !!v.voice_cloning_enabled, is_active: v.is_active !== false,
});

export default function AdminPlans() {
  const { open, editItem, openModal, openEdit, closeModal } = useModal();
  const [plans, setPlans] = useState([]);
  const [error, setError] = useState("");
  const load = () => fetchAdminPlans().then(d => setPlans(Array.isArray(d) ? d : d?.results || [])).catch(e => setError(e.message));
  useEffect(() => { load(); }, []);

  return (
    <div>
      <AdminPageHeader title="Tariflar" subtitle="Obuna sahifasida ko'rinadigan tariflar"
        action={<button className="btn btn-primary" onClick={openModal}>+ Yangi tarif</button>} />
      {error && <div className="math-feedback wrong">{error}</div>}
      <div className="admin-table">
        <div className="admin-table-head" style={{ gridTemplateColumns: "1.2fr 0.8fr 0.8fr 2fr 0.8fr 0.6fr" }}>
          <div>Nomi</div><div>Narx</div><div>Muddat</div><div>Imkoniyatlar</div><div>Obunachilar</div><div></div>
        </div>
        {plans.map(p => (
          <div key={p.id} className="admin-table-row" style={{ gridTemplateColumns: "1.2fr 0.8fr 0.8fr 2fr 0.8fr 0.6fr" }}>
            <div><b>{p.name}</b> {!p.is_active && <span className="badge off">sotuvda emas</span>}</div>
            <div>${p.price_usd}</div>
            <div>{p.duration_days} kun</div>
            <div style={{ fontSize: 13, color: "var(--text-muted)" }}>{(p.features || []).join(" · ") || "—"}</div>
            <div>{p.subscribers}</div>
            <div><RowActions onEdit={() => openEdit(p)} onDelete={async () => {
              const r = await deleteAdminPlan(p.id).catch(e => setError(e.message));
              if (r?.detail) setError(r.detail);
              load();
            }} deleteLabel="Tarifni o'chirasizmi?" /></div>
          </div>
        ))}
      </div>
      {open && (
        <AddModal
          title={editItem ? "Tarifni tahrirlash" : "Yangi tarif"}
          initialValues={editItem ? { ...editItem, features: (editItem.features || []).join("\n") } : { duration_days: 30, is_active: true }}
          fields={FIELDS}
          onSubmit={async v => { editItem ? await updateAdminPlan(editItem.id, toPayload(v)) : await createAdminPlan(toPayload(v)); load(); }}
          onClose={closeModal}
        />
      )}
    </div>
  );
}
