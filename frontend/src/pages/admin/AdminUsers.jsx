import React, { useEffect, useState } from "react";
import { adminUsers as mockUsers } from "../../data/mockData.js";
import { fetchAdminUsers, createAdminUser, updateAdminUser, deleteAdminUser } from "../../api/client.js";
import { AddModal, useModal, AdminPageHeader, RowActions, DemoBanner } from "./AdminLayout.jsx";

const initialColors = ["oklch(0.6 0.15 275)", "oklch(0.6 0.15 25)", "oklch(0.6 0.15 155)", "oklch(0.65 0.15 85)"];

function initials(name) {
  return (name || "?").split(" ").map(p => p[0]).slice(0, 2).join("").toUpperCase();
}

export default function AdminUsers() {
  const { open, editItem, openModal, openEdit, closeModal } = useModal();
  const [users, setUsers] = useState(mockUsers.map(u => ({ ...u, id: null })));
  const [isDemo, setIsDemo] = useState(false);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  function load(searchTerm) {
    setLoading(true);
    fetchAdminUsers(searchTerm)
      .then(data => {
        setIsDemo(false);
        setUsers((data || []).map(u => ({
          id: u.id, name: u.username, email: u.email, phone: u.phone,
          subject: "—", level: "—", premium: u.is_premium, staff: u.is_staff, active: u.is_active,
        })));
      })
      .catch(err => {
        if (err.isNetworkError) setIsDemo(true);
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  useEffect(() => {
    const id = setTimeout(() => { if (!isDemo) load(search); }, 350);
    return () => clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  return (
    <div>
      <AdminPageHeader
        title="Foydalanuvchilar"
        subtitle={`Jami ${users.length} ta ro'yxatdan o'tgan foydalanuvchi`}
        action={<button className="btn btn-primary" onClick={openModal}>+ Yangi foydalanuvchi</button>}
      />
      <DemoBanner show={isDemo} />
      <input
        className="input admin-search" placeholder="Foydalanuvchi qidirish..." style={{ marginBottom: 16 }}
        value={search} onChange={e => setSearch(e.target.value)} disabled={isDemo}
      />
      <div className="admin-table">
        <div className="admin-table-head" style={{ gridTemplateColumns: "2fr 1fr 0.9fr 0.9fr 0.7fr" }}>
          <div>Foydalanuvchi</div><div>Telefon</div><div>Holat</div><div>Rol</div><div></div>
        </div>
        {users.map((u, i) => (
          <div key={u.id ?? i} className="admin-table-row" style={{ gridTemplateColumns: "2fr 1fr 0.9fr 0.9fr 0.7fr" }}>
            <div className="user-cell">
              <div className="avatar-initial" style={{ background: initialColors[i % initialColors.length] }}>{initials(u.name)}</div>
              <div>
                <div className="user-name">{u.name}</div>
                <div className="user-email">{u.email}</div>
              </div>
            </div>
            <div>{u.phone || "—"}</div>
            <div>
              <span className={"badge " + (u.premium ? "on" : "off")}>{u.premium ? "Premium" : "Free"}</span>
              {u.active === false && <span className="badge off" style={{ marginLeft: 6 }}>Faolsiz</span>}
            </div>
            <div>{u.staff ? "Admin" : "O'quvchi"}</div>
            <div>
              {u.id && (
                <RowActions
                  onEdit={() => openEdit(u)}
                  onDelete={async () => {
                    await deleteAdminUser(u.id);
                    setUsers(list => list.map(x => x.id === u.id ? { ...x, active: false } : x));
                  }}
                  deleteLabel="Foydalanuvchini faolsizlantirmoqchimisiz? (ma'lumotlari o'chirilmaydi)"
                />
              )}
            </div>
          </div>
        ))}
        {!loading && users.length === 0 && (
          <div style={{ padding: 24, textAlign: "center", color: "var(--text-muted)" }}>Hech kim topilmadi</div>
        )}
      </div>

      {open && !editItem && (
        <AddModal
          title="Yangi foydalanuvchi qo'shish"
          fields={[
            { name: "username", label: "Foydalanuvchi nomi" },
            { name: "email", label: "Email" },
            { name: "phone", label: "Telefon" },
          ]}
          onSubmit={async (v) => {
            const created = await createAdminUser(v);
            setUsers(u => [{ id: created.id, name: created.username, email: created.email, phone: created.phone, subject: "—", level: "—", premium: false, staff: false, active: true }, ...u]);
          }}
          onClose={closeModal}
        />
      )}
      {open && editItem && (
        <AddModal
          title={`${editItem.name} — tahrirlash`}
          initialValues={{ email: editItem.email, phone: editItem.phone, is_premium: editItem.premium, is_staff: editItem.staff, is_active: editItem.active }}
          fields={[
            { name: "email", label: "Email" },
            { name: "phone", label: "Telefon" },
            { name: "is_premium", label: "Premium a'zolik", type: "checkbox" },
            { name: "is_staff", label: "Admin huquqi", type: "checkbox" },
            { name: "is_active", label: "Faol", type: "checkbox" },
          ]}
          onSubmit={async (v) => {
            const updated = await updateAdminUser(editItem.id, v);
            setUsers(list => list.map(x => x.id === editItem.id
              ? { ...x, email: updated.email, phone: updated.phone, premium: updated.is_premium, staff: updated.is_staff, active: updated.is_active }
              : x));
          }}
          onClose={closeModal}
        />
      )}
    </div>
  );
}
