import React, { useEffect, useState } from "react";
import { fetchFlashcards, createFlashcard, updateFlashcard, deleteFlashcard, fetchSubjects } from "../../api/client.js";
import { AddModal, useModal, AdminPageHeader, RowActions } from "./AdminLayout.jsx";

export default function AdminFlashcards() {
  const { open, editItem, openModal, openEdit, closeModal } = useModal();
  const [cards, setCards] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    try {
      const [fc, subs] = await Promise.all([fetchFlashcards(), fetchSubjects()]);
      setCards(Array.isArray(fc) ? fc : (fc?.results || []));
      setSubjects(Array.isArray(subs) ? subs : (subs?.results || []));
    } catch (e) { setError(e.message || "Flashcardlar yuklanmadi."); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);

  async function save(values) {
    const payload = { ...values, subject: Number(values.subject) };
    if (editItem) {
      const updated = await updateFlashcard(editItem.id, payload);
      setCards(list => list.map(x => x.id === editItem.id ? updated : x));
    } else {
      const created = await createFlashcard(payload);
      setCards(list => [created, ...list]);
    }
  }

  const subjectOptions = subjects.map(s => ({ value: String(s.id), label: s.name }));

  return (
    <div>
      <AdminPageHeader title="Flashcardlar" subtitle="Spaced Repetition uchun karta bankini boshqarish"
        action={<button className="btn btn-primary" onClick={openModal}>+ Yangi karta</button>} />
      {error && <div className="math-feedback wrong">{error}</div>}
      {loading ? <div className="page-sub">Yuklanmoqda...</div> : (
        <div className="admin-table">
          <div className="admin-table-head" style={{ gridTemplateColumns: "1fr 1.5fr 1.5fr 1fr .5fr" }}>
            <div>Fan</div><div>Old tomoni</div><div>Javob</div><div>Audio</div><div></div>
          </div>
          {cards.map(c => (
            <div key={c.id} className="admin-table-row" style={{ gridTemplateColumns: "1fr 1.5fr 1.5fr 1fr .5fr" }}>
              <div>{c.subject_name || "—"}</div><div>{c.front_text}</div><div>{c.back_text}</div>
              <div>{c.audio_url ? "Bor" : "—"}</div>
              <RowActions onEdit={() => openEdit(c)} onDelete={async () => {
                await deleteFlashcard(c.id); setCards(list => list.filter(x => x.id !== c.id));
              }} />
            </div>
          ))}
        </div>
      )}
      {open && <AddModal title={editItem ? "Flashcardni tahrirlash" : "Yangi flashcard"}
        initialValues={editItem || {}} fields={[
          { name: "subject", label: "Fan", type: "select", options: subjectOptions },
          { name: "front_text", label: "Old tomoni" },
          { name: "back_text", label: "Javob / tarjima" },
          { name: "audio_url", label: "Audio URL (ixtiyoriy)" },
        ]} onSubmit={save} onClose={closeModal} />}
    </div>
  );
}
