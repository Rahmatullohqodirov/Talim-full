import React, { useEffect, useState } from "react";
import { adminProblems as mockProblems } from "../../data/mockData.js";
import { fetchMathProblems, createMathProblem, updateMathProblem, deleteMathProblem } from "../../api/client.js";
import { AddModal, useModal, AdminPageHeader, RowActions, DemoBanner } from "./AdminLayout.jsx";

const diffLabel = { 1: "Oson", 2: "O'rta", 3: "Qiyin" };
const diffOptions = [{ value: "1", label: "Oson" }, { value: "2", label: "O'rta" }, { value: "3", label: "Qiyin" }];

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
        <div className="admin-table-head" style={{ gridTemplateColumns: "1.2fr 1.8fr 0.8fr 0.5fr" }}>
          <div>Mavzu</div><div>Masala</div><div>Qiyinlik</div><div></div>
        </div>
        {problems.map((p, i) => (
          <div key={p.id ?? i} className="admin-table-row" style={{ gridTemplateColumns: "1.2fr 1.8fr 0.8fr 0.5fr" }}>
            <div style={{ fontWeight: 600 }}>{p.topic}</div>
            <div style={{ color: "var(--text-muted)", fontFamily: "monospace" }}>{p.statement}</div>
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
            { name: "topic_name", label: "Mavzu (masalan: Algebra)" },
            { name: "statement", label: "Masala matnni" },
            { name: "difficulty", label: "Qiyinlik", type: "select", options: diffOptions },
          ]}
          onSubmit={async (v) => {
            const created = await createMathProblem({ ...v, difficulty: Number(v.difficulty), solution_steps: [] });
            setProblems(p => [{ id: created.id, topicId: created.topic, topic: v.topic_name, statement: created.statement, difficulty: created.difficulty, difficultyLabel: diffLabel[created.difficulty] }, ...p]);
          }}
          onClose={closeModal}
        />
      )}
      {open && editItem && (
        <AddModal
          title="Masalani tahrirlash"
          initialValues={{ statement: editItem.statement, difficulty: String(editItem.difficulty) }}
          fields={[
            { name: "statement", label: "Masala matni" },
            { name: "difficulty", label: "Qiyinlik", type: "select", options: diffOptions },
          ]}
          onSubmit={async (v) => {
            const updated = await updateMathProblem(editItem.id, { statement: v.statement, difficulty: Number(v.difficulty) });
            setProblems(list => list.map(x => x.id === editItem.id
              ? { ...x, statement: updated.statement, difficulty: updated.difficulty, difficultyLabel: diffLabel[updated.difficulty] }
              : x));
          }}
          onClose={closeModal}
        />
      )}
    </div>
  );
}
