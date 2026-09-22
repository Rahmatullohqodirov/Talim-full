import React, { useEffect, useState } from "react";
import { fetchMathProblems, submitMathAnswer } from "../../api/client.js";
import "./MathPractice.css";

export default function MathPractice() {
  const [problems, setProblems] = useState([]);
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [stepsRevealed, setStepsRevealed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [score, setScore] = useState({ correct: 0, total: 0 });

  useEffect(() => {
    fetchMathProblems()
      .then(data => setProblems(Array.isArray(data) ? data : (data?.results || [])))
      .catch(e => setError(e.message || "Masalalarni yuklab bo'lmadi."))
      .finally(() => setLoading(false));
  }, []);

  const problem = problems[index];

  function nextProblem() {
    if (!problems.length) return;
    setIndex(i => (i + 1) % problems.length);
    setAnswer("");
    setFeedback(null);
    setStepsRevealed(false);
  }

  async function submit() {
    if (!problem || !answer.trim()) return;
    try {
      const res = await submitMathAnswer(problem.id, { user_answer: answer });
      setFeedback({
        correct: !!res.is_correct,
        text: res.is_correct ? "To'g'ri javob! 🎉" : "Noto'g'ri. Yechim qadamlarini ko'rib, yana urinib ko'ring."
      });
      setScore(s => ({ correct: s.correct + (res.is_correct ? 1 : 0), total: s.total + 1 }));
    } catch (e) {
      setError(e.message || "Javobni tekshirib bo'lmadi.");
    }
  }

  return (
    <div>
      <h1 className="page-title" style={{ marginBottom: 8 }}>Matematika mashqlari</h1>
      <p className="page-sub">Masalalar backenddan olinadi · 5 ta asosiy fan katalogi mavjud</p>

      {loading && <div className="page-sub">Yuklanmoqda...</div>}
      {error && <div className="math-feedback wrong">{error}</div>}
      {!loading && !problem && !error && <div className="page-sub">Hozircha masalalar mavjud emas.</div>}

      {problem && (
        <div className="math-grid">
          <div className="math-card">
            <div className="math-topic">{problem.topic_name || "Matematika"} · {problem.difficulty_label || problem.difficulty}</div>
            <div style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 8 }}>Masala {index + 1} / {problems.length} · Natija {score.correct}/{score.total}</div>
            <div className="math-statement">{problem.statement}</div>
            <input className="input" style={{ marginBottom: 14 }} placeholder="Javobingiz" value={answer} onChange={e => setAnswer(e.target.value)}
              onKeyDown={e => e.key === "Enter" && submit()} />
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <button className="btn btn-primary" onClick={submit}>Tekshirish</button>
              <button className="btn btn-outline" onClick={() => setStepsRevealed(v => !v)}>{stepsRevealed ? "Yechimni yashirish" : "Yechimni ko'rsat"}</button>
              <button className="btn btn-outline" onClick={nextProblem}>Keyingi masala →</button>
            </div>
            {feedback && <div className={"math-feedback " + (feedback.correct ? "correct" : "wrong")}>{feedback.text}</div>}
            {stepsRevealed && problem.solution_steps?.length > 0 && (
              <div className="steps-list">
                <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 8, color: "var(--text-muted)" }}>Qadamlar:</div>
                {problem.solution_steps.map((s, i) => <div key={i} className="step-line">{s}</div>)}
              </div>
            )}
          </div>
          <div className="weak-panel">
            <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>Mavzular</div>
            {[...new Set(problems.map(p => p.topic_name).filter(Boolean))].map(topic => (
              <div key={topic} className="weak-row"><span>{topic}</span><span style={{ fontWeight: 700 }}>{problems.filter(p => p.topic_name === topic).length} ta</span></div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
