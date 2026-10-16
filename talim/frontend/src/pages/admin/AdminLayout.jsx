import React, { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useApp } from "../../context/AppContext.jsx";
import StatusPill from "../../components/StatusPill.jsx";
import "./Admin.css";

const navItems = [
  { to: "stats", label: "Statistika", icon: "▤" },
  { to: "users", label: "Foydalanuvchilar", icon: "◉" },
  { to: "tickets", label: "Murojaatlar", icon: "✉" },
  { to: "payments", label: "To'lovlar", icon: "◇" },
  { to: "plans", label: "Tariflar", icon: "★" },
  { to: "quizzes", label: "Quizlar", icon: "?" },
  { to: "lessons", label: "Darslar", icon: "▤" },
  { to: "stories", label: "Tinglang-o'qing", icon: "▶" },
  { to: "problems", label: "Masalalar", icon: "∑" },
  { to: "flashcards", label: "Flashcardlar", icon: "▣" },
  { to: "videos", label: "Videolar", icon: "▶" },
  { to: "avatars", label: "Avatarlar", icon: "◐" },
  { to: "subjects", label: "Fanlar", icon: "▦" },
  { to: "leaderboard", label: "Reyting", icon: "#" },
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
  const { logout } = useApp();
  const navigate = useNavigate();
  return (
    <div className="admin-shell">
      <aside className="admin-sidebar">
        <div className="admin-brand">Talim</div>
        <div className="admin-sidebar-eyebrow">BOSHQARUV</div>
        <div className="admin-sidebar-title">Admin panel</div>
        <div style={{ padding: "0 12px 18px" }}><StatusPill /></div>
        {navItems.map(n => (
          <NavLink key={n.to} to={n.to} className={({ isActive }) => "admin-nav-item" + (isActive ? " active" : "")}>
            <span className="admin-icon">{n.icon}</span>
            <span>{n.label}</span>
          </NavLink>
        ))}
        <button type="button" className="admin-logout" onClick={() => { logout(); navigate("/"); }}>Chiqish</button>
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
        <div className="modal-fields">
          {fields.map(f => (
            <label key={f.name} className={"modal-field" + (f.type === "checkbox" ? " check" : "")}>
              {f.type !== "checkbox" && <span className="modal-label">{f.label}</span>}
              {f.type === "select" ? (
                <select className="input" value={values[f.name] ?? ""} onChange={e => setField(f.name, e.target.value)}>
                  <option value="" disabled>Tanlang</option>
                  {f.options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              ) : f.type === "checkbox" ? (
                <>
                  <input type="checkbox" checked={!!values[f.name]} onChange={e => setField(f.name, e.target.checked)} />
                  {f.label}
                </>
              ) : f.type === "textarea" ? (
                <textarea className="input modal-textarea" rows={f.rows || 4} placeholder={f.placeholder || ""}
                  value={values[f.name] ?? ""} onChange={e => setField(f.name, e.target.value)} />
              ) : (
                <input className="input" type={f.type || "text"} placeholder={f.placeholder || ""} value={values[f.name] ?? ""}
                  onChange={e => setField(f.name, e.target.value)} />
              )}
              {f.help && <span className="modal-help">{f.help}</span>}
            </label>
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
