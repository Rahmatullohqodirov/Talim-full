import React, { useEffect, useState } from "react";
import { adminAvatars as mockAvatars } from "../../data/mockData.js";
import { fetchAvatars, createAvatarAdmin, updateAvatarAdmin, deleteAvatarAdmin } from "../../api/client.js";
import { AddModal, useModal, AdminPageHeader, RowActions, DemoBanner } from "./AdminLayout.jsx";

const genderOptions = [{ value: "female", label: "Ayol" }, { value: "male", label: "Erkak" }];

export default function AdminAvatars() {
  const { open, editItem, openModal, openEdit, closeModal } = useModal();
  const [avatars, setAvatars] = useState(mockAvatars.map(a => ({ ...a, id: null })));
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    fetchAvatars()
      .then(data => {
        setIsDemo(false);
        setAvatars((data || []).map(a => ({
          id: a.id, name: a.name, gender: a.gender,
          genderLabel: a.gender === "male" ? "Erkak" : "Ayol", premium: a.is_premium_only,
        })));
      })
      .catch(err => { if (err.isNetworkError) setIsDemo(true); });
  }, []);

  return (
    <div>
      <AdminPageHeader
        title="Avatarlar"
        subtitle="Lip-sync avatarlar va ovoz modeli sozlamalari"
        action={<button className="btn btn-primary" onClick={openModal}>+ Yangi avatar</button>}
      />
      <DemoBanner show={isDemo} />
      <div className="grid-4">
        {avatars.map((a, i) => (
          <div key={a.id ?? i} className="avatar-tile">
            <div className="avatar-thumb" />
            <div style={{ fontWeight: 700, fontSize: 14.5 }}>{a.name}</div>
            <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>{a.genderLabel || a.gender}</div>
            {a.premium && <span className="badge on" style={{ marginTop: 8, display: "inline-block" }}>Premium</span>}
            {a.id && (
              <div className="tile-actions" style={{ justifyContent: "center" }}>
                <RowActions
                  onEdit={() => openEdit(a)}
                  onDelete={async () => {
                    await deleteAvatarAdmin(a.id);
                    setAvatars(list => list.filter(x => x.id !== a.id));
                  }}
                  deleteLabel={`"${a.name}" avatarini o'chirmoqchimisiz?`}
                />
              </div>
            )}
          </div>
        ))}
      </div>

      {open && !editItem && (
        <AddModal
          title="Yangi avatar qo'shish"
          fields={[
            { name: "name", label: "Ismi" },
            { name: "gender", label: "Jinsi", type: "select", options: genderOptions },
            { name: "is_premium_only", label: "Faqat premium uchun", type: "checkbox" },
          ]}
          onSubmit={async (v) => {
            const created = await createAvatarAdmin({ ...v, voice_model_id: (v.name || "avatar").toLowerCase() + "-default" });
            setAvatars(a => [{ id: created.id, name: created.name, gender: created.gender, genderLabel: created.gender === "male" ? "Erkak" : "Ayol", premium: created.is_premium_only }, ...a]);
          }}
          onClose={closeModal}
        />
      )}
      {open && editItem && (
        <AddModal
          title={`${editItem.name} — tahrirlash`}
          initialValues={{ name: editItem.name, gender: editItem.gender, is_premium_only: editItem.premium }}
          fields={[
            { name: "name", label: "Ismi" },
            { name: "gender", label: "Jinsi", type: "select", options: genderOptions },
            { name: "is_premium_only", label: "Faqat premium uchun", type: "checkbox" },
          ]}
          onSubmit={async (v) => {
            const updated = await updateAvatarAdmin(editItem.id, v);
            setAvatars(list => list.map(x => x.id === editItem.id
              ? { ...x, name: updated.name, gender: updated.gender, genderLabel: updated.gender === "male" ? "Erkak" : "Ayol", premium: updated.is_premium_only }
              : x));
          }}
          onClose={closeModal}
        />
      )}
    </div>
  );
}
