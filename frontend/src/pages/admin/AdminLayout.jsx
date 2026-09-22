import React, { useState } from "react";
import { NavLink, Outlet, Link } from "react-router-dom";
import StatusPill from "../../components/StatusPill.jsx";
import "./Admin.css";

const navItems = [
  { to: "users", label: "Foydalanuvchilar", icon: "◉" },
  { to: "subjects", label: "Fanlar", icon: "▦" },
  { to: "avatars", label: "Avatarlar", icon: "◐" },
  { to: "problems", label: "Masalalar", icon: "∑" },
  { to: "flashcards", label: "Flashcardlar", icon: "▣" },
  { to: "leaderboard", label: "Leaderboard", icon: "🏆" },
  { to: "videos", label: "Videolar", icon: "▶" },
  { to: "payments", label: "To'lovlar", icon: "◇" },
  { to: "stats", label: "Statistika", icon: "▤" },
];

export { StatusPill };


export function DemoBanner({ show, text }) {
  if (!show) return null;
  return (
    <div className="demo-banner">
      ⚠ {text || "Backend serverga ulanib bo'lmadi — hozir demo (namunaviy) ma'lumotlar ko'rsatilmoqda. O'zgarishlar backend qayta ulangach saqlanadi."}
    </div>
  );
}

export default function AdminLayout() {
  return (
    <div className="admin-shell">
      <aside className="admin-sidebar">
        <Link to="/app/dashboard" className="admin-back">← Ilovaga qaytish</Link>
        <div className="admin-sidebar-eyebrow">BOSHQARUV</div>
        <div className="admin-sidebar-title">Admin panel</div>
        <div style={{ padding: "0 12px 18px" }}><StatusPill /></div>
        {navItems.map(n => (
          <NavLink key={n.to} to={n.to} className={({ isActive }) => "admin-nav-item" + (isActive ? " active" : "")}>
            <span className="admin-icon">{n.icon}</span>
            <span>{n.label}</span>
          </NavLink>
        ))}
      </aside>
      <div className="admin-content">
        <Outlet />
      </div>
    </div>
  );
}

export function AdminPageHeader({ title, subtitle, action }) {
  return (
    <div className="admin-page-header">
      <div>
        <div className="admin-page-title">{title}</div>
        <p className="admin-page-sub">{subtitle}</p>
      </div>
      {action}
    </div>
  );
}

/**
 * Qo'shish HAM tahrirlash uchun ishlatiladigan modal.
 * `initialValues` berilsa — tahrirlash rejimi (mavjud qiymatlar bilan to'ldiriladi).
 */
export function AddModal({ title, fields, onSubmit, onClose, initialValues, submitLabel }) {
  const [values, setValues] = useState(initialValues || {});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const isEdit = !!initialValues;

  function setField(name, value) {
    setValues(v => ({ ...v, [name]: value }));
  }

  async function handleSave() {
    setSaving(true);
    setError("");
    try {
      await onSubmit(values);
      onClose();
    } catch (e) {
      setError(e.message || "Xatolik yuz berdi");
    }
    setSaving(false);
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-panel" onClick={e => e.stopPropagation()}>
        <div style={{ fontWeight: 800, fontSize: 18, fontFamily: "var(--font-display)", marginBottom: 20 }}>{title}</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {fields.map(f => (
            f.type === "select" ? (
              <select key={f.name} className="input" value={values[f.name] ?? ""} onChange={e => setField(f.name, e.target.value)}>
                <option value="" disabled>{f.label}</option>
                {f.options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            ) : f.type === "checkbox" ? (
              <label key={f.name} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 13.5, fontWeight: 600 }}>
                <input type="checkbox" checked={!!values[f.name]} onChange={e => setField(f.name, e.target.checked)} />
                {f.label}
              </label>
            ) : (
              <input key={f.name} className="input" placeholder={f.label} value={values[f.name] ?? ""}
                     onChange={e => setField(f.name, e.target.value)} />
            )
          ))}
        </div>
        {error && <div style={{ color: "oklch(0.6 0.2 25)", fontSize: 13, marginTop: 10 }}>{error}</div>}
        <div style={{ display: "flex", gap: 10, marginTop: 24 }}>
          <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleSave} disabled={saving}>
            {saving ? "Saqlanmoqda..." : (submitLabel || (isEdit ? "Yangilash" : "Saqlash"))}
          </button>
          <button className="btn btn-outline" style={{ flex: 1 }} onClick={onClose}>Bekor qilish</button>
        </div>
      </div>
    </div>
  );
}

export function useModal() {
  const [open, setOpen] = useState(false);
  const [editItem, setEditItem] = useState(null);
  return {
    open,
    editItem,
    openModal: () => { setEditItem(null); setOpen(true); },
    openEdit: (item) => { setEditItem(item); setOpen(true); },
    closeModal: () => { setOpen(false); setEditItem(null); },
  };
}

/** Jadval qatorlarida tahrirlash/o'chirish tugmalari. */
export function RowActions({ onEdit, onDelete, deleteLabel = "O'chirishni tasdiqlaysizmi?" }) {
  return (
    <div className="row-actions">
      {onEdit && (
        <button className="icon-btn" title="Tahrirlash" onClick={onEdit}>✎</button>
      )}
      {onDelete && (
        <button
          className="icon-btn danger"
          title="O'chirish"
          onClick={() => { if (window.confirm(deleteLabel)) onDelete(); }}
        >
          🗑
        </button>
      )}
    </div>
  );
}
