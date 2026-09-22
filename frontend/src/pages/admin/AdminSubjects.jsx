import React, { useEffect, useState } from "react";
import { adminSubjects as mockSubjects } from "../../data/mockData.js";
import { fetchSubjects, createSubject, updateSubject, deleteSubject } from "../../api/client.js";
import { AddModal, useModal, AdminPageHeader, RowActions, DemoBanner } from "./AdminLayout.jsx";

const kindOptions = [{ value: "language", label: "Til" }, { value: "math", label: "Matematika" }];

export default function AdminSubjects() {
  const { open, editItem, openModal, openEdit, closeModal } = useModal();
  const [subjects, setSubjects] = useState(mockSubjects.map(s => ({ ...s, id: null })));
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    fetchSubjects()
      .then(data => {
        setIsDemo(false);
        setSubjects((data || []).map(s => ({
          id: s.id, code: s.code, name: s.name, kind: s.kind,
          kindLabel: s.kind === "math" ? "Fan" : "Til", levels: (s.levels || []).length, active: s.is_active_in_mvp,
        })));
      })
      .catch(err => { if (err.isNetworkError) setIsDemo(true); });
  }, []);

  return (
    <div>
      <AdminPageHeader
        title="Fanlar"
        subtitle="Til va matematika fanlari, CEFR darajalari"
        action={<button className="btn btn-primary" onClick={openModal}>+ Yangi fan</button>}
      />
      <DemoBanner show={isDemo} />
      <div className="grid-3">
        {subjects.map((s, i) => (
          <div key={s.id ?? i} className="subject-tile">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <div style={{ fontWeight: 700, fontSize: 15.5 }}>{s.name}</div>
              <span className={"badge " + (s.active ? "on" : "off")}>{s.active ? "MVP faol" : "Kutilmoqda"}</span>
            </div>
            <div style={{ fontSize: 12.5, color: "var(--text-muted)" }}>{s.kindLabel || s.kind} &middot; {s.levels} daraja</div>
            {s.id && (
              <div className="tile-actions">
                <RowActions
                  onEdit={() => openEdit(s)}
                  onDelete={async () => {
                    await deleteSubject(s.id);
                    setSubjects(list => list.filter(x => x.id !== s.id));
                  }}
                  deleteLabel={`"${s.name}" fanini o'chirmoqchimisiz?`}
                />
              </div>
            )}
          </div>
        ))}
      </div>

      {open && !editItem && (
        <AddModal
          title="Yangi fan qo'shish"
          fields={[
            { name: "code", label: "Kod (masalan: german)" },
            { name: "name", label: "Nomi (masalan: Nemis tili)" },
            { name: "kind", label: "Turi", type: "select", options: kindOptions },
            { name: "is_active_in_mvp", label: "MVP'da faol", type: "checkbox" },
          ]}
          onSubmit={async (v) => {
            const created = await createSubject(v);
            setSubjects(s => [{ id: created.id, code: created.code, name: created.name, kind: created.kind, kindLabel: created.kind === "math" ? "Fan" : "Til", levels: 0, active: created.is_active_in_mvp }, ...s]);
          }}
          onClose={closeModal}
        />
      )}
      {open && editItem && (
        <AddModal
          title={`${editItem.name} — tahrirlash`}
          initialValues={{ code: editItem.code, name: editItem.name, kind: editItem.kind, is_active_in_mvp: editItem.active }}
          fields={[
            { name: "code", label: "Kod" },
            { name: "name", label: "Nomi" },
            { name: "kind", label: "Turi", type: "select", options: kindOptions },
            { name: "is_active_in_mvp", label: "MVP'da faol", type: "checkbox" },
          ]}
          onSubmit={async (v) => {
            const updated = await updateSubject(editItem.id, v);
            setSubjects(list => list.map(x => x.id === editItem.id
              ? { ...x, code: updated.code, name: updated.name, kind: updated.kind, kindLabel: updated.kind === "math" ? "Fan" : "Til", active: updated.is_active_in_mvp }
              : x));
          }}
          onClose={closeModal}
        />
      )}
    </div>
  );
}
