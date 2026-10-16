import React, { useEffect, useState } from "react";
import { adminProblems as mockProblems } from "../../data/mockData.js";
import { fetchMathProblems, createMathProblem, updateMathProblem, deleteMathProblem } from "../../api/client.js";
import { AddModal, useModal, AdminPageHeader, RowActions, DemoBanner } from "./AdminLayout.jsx";

const diffLabel = { 1: "Oson", 2: "O'rta", 3: "Qiyin" };
const diffOptions = [{ value: "1", label: "Oson" }, { value: "2", label: "O'rta" }, { value: "3", label: "Qiyin" }];

function toPayload(v) {
  const steps = String(v.steps || "").split("\n").map(x => x.trim()).filter(Boolean);
  const answers = String(v.answers || "").split(";").map(x => x.trim()).filter(Boolean);
  return { topic_name: v.topic_name, statement: v.statement, difficulty: Number(v.difficulty || 1), solution_steps: steps, answers };
}

export default function AdminProblems() {
  const { open, editItem, openModal, openEdit, closeModal } = useModal();
  const [problems, setProblems] = useState(mockProblems.map(p => ({ ...p, id: null })));
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    fetchMathProblems()
      .then(data => {
        setIsDemo(false);
        setProblems((data || []).map(p => ({
          id: p.id, topicId: p.topic, topic: p.topic_name || "—", statement: p.statement,
          difficulty: p.difficulty, difficultyLabel: diffLabel[p.difficulty] || p.difficulty,
          steps: p.solution_steps || [], answers: p.answers || [],
        })));
      })
      .catch(err => { if (err.isNetworkError) setIsDemo(true); });
  }, []);

  return (
    <div>
      <AdminPageHeader
        title="Matematika masalalari"
        subtitle="Mavzu va qiyinlik darajasi bo'yicha masalalar banki"
        action={<button className="btn btn-primary" onClick={openModal}>+ Yangi masala</button>}
      />
      <DemoBanner show={isDemo} />
      <div className="admin-table">
        <div className="admin-table-head" style={{ gridTemplateColumns: "1fr 2fr 0.8fr 0.7fr 0.5fr" }}>
          <div>Mavzu</div><div>Masala</div><div>Javob</div><div>Qiyinlik</div><div></div>
        </div>
        {problems.map((p, i) => (
          <div key={p.id ?? i} className="admin-table-row" style={{ gridTemplateColumns: "1fr 2fr 0.8fr 0.7fr 0.5fr" }}>
            <div style={{ fontWeight: 600 }}>{p.topic}</div>
            <div style={{ color: "var(--text-muted)" }}>{p.statement}</div>
            <div>{p.answers?.length ? p.answers.join("; ") : <span className="badge off">o'zi baholaydi</span>}</div>
            <div>{p.difficultyLabel || p.difficulty}</div>
            <div>
              {p.id && (
                <RowActions
                  onEdit={() => openEdit(p)}
                  onDelete={async () => {
                    await deleteMathProblem(p.id);
                    setProblems(list => list.filter(x => x.id !== p.id));
                  }}
                  deleteLabel="Bu masalani o'chirmoqchimisiz?"
                />
              )}
            </div>
          </div>
        ))}
      </div>

      {open && !editItem && (
        <AddModal
          title="Yangi masala qo'shish"
          fields={[
            { name: "topic_name", label: "Mavzu", placeholder: "masalan: Algebra" },
            { name: "statement", label: "Masala matni", type: "textarea", rows: 3 },
            { name: "steps", label: "Yechim qadamlari", type: "textarea", rows: 5, placeholder: "2x = 10\nx = 5", help: "Har bir qadam alohida qatorda." },
            { name: "answers", label: "To'g'ri javob", placeholder: "5   yoki   2; 3", help: "Bir nechta javob bo'lsa ; bilan ajrating. Bo'sh qoldirilsa — oxirgi qadamdan avtomatik olinadi; isbot masalalarida bo'sh qoladi." },
            { name: "difficulty", label: "Qiyinlik", type: "select", options: diffOptions },
          ]}
          onSubmit={async (v) => {
            const created = await createMathProblem(toPayload(v));
            setProblems(p => [{ id: created.id, topicId: created.topic, topic: v.topic_name, statement: created.statement, difficulty: created.difficulty, difficultyLabel: diffLabel[created.difficulty], steps: created.solution_steps, answers: created.answers }, ...p]);
          }}
          onClose={closeModal}
        />
      )}
      {open && editItem && (
        <AddModal
          title="Masalani tahrirlash"
          initialValues={{ statement: editItem.statement, difficulty: String(editItem.difficulty),
            steps: (editItem.steps || []).join("\n"), answers: (editItem.answers || []).join("; ") }}
          fields={[
            { name: "statement", label: "Masala matni", type: "textarea", rows: 3 },
            { name: "steps", label: "Yechim qadamlari", type: "textarea", rows: 5, placeholder: "2x = 10\nx = 5", help: "Har bir qadam alohida qatorda." },
            { name: "answers", label: "To'g'ri javob", placeholder: "5   yoki   2; 3", help: "Bir nechta javob bo'lsa ; bilan ajrating. Bo'sh qoldirilsa — oxirgi qadamdan avtomatik olinadi; isbot masalalarida bo'sh qoladi." },
            { name: "difficulty", label: "Qiyinlik", type: "select", options: diffOptions },
          ]}
          onSubmit={async (v) => {
            const { topic_name, ...payload } = toPayload(v);
            const updated = await updateMathProblem(editItem.id, payload);
            setProblems(list => list.map(x => x.id === editItem.id
              ? { ...x, statement: updated.statement, difficulty: updated.difficulty, difficultyLabel: diffLabel[updated.difficulty], steps: updated.solution_steps, answers: updated.answers }
              : x));
          }}
          onClose={closeModal}
        />
      )}
    </div>
  );
}
