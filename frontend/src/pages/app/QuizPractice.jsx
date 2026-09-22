import React, { useEffect, useMemo, useState } from "react";
import { fetchQuizzes, submitQuizAttempt } from "../../api/client.js";
import { useOnlineStatus } from "../../hooks/useOnlineStatus.js";
import "./QuizPractice.css";

const CACHE_KEY = "st_quiz_cache_v1";
const PENDING_KEY = "st_quiz_pending_attempts_v1";

function loadCachedQuizzes() {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
}

function saveCachedQuizzes(quizzes) {
  try { localStorage.setItem(CACHE_KEY, JSON.stringify(quizzes)); } catch { /* xotira to'lgan bo'lishi mumkin */ }
}

function loadPending() {
  try {
    const raw = localStorage.getItem(PENDING_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
}

function savePending(list) {
  try { localStorage.setItem(PENDING_KEY, JSON.stringify(list)); } catch { /* ignore */ }
}

export default function QuizPractice() {
  const { isOnline } = useOnlineStatus();
  const [quizzes, setQuizzes] = useState(() => loadCachedQuizzes());
  const [usingCache, setUsingCache] = useState(false);
  const [activeQuiz, setActiveQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [pendingCount, setPendingCount] = useState(() => loadPending().length);

  useEffect(() => {
    fetchQuizzes()
      .then(data => {
        const list = Array.isArray(data) ? data : (data?.results || []);
        if (list.length) {
          setQuizzes(list);
          saveCachedQuizzes(list);
          setUsingCache(false);
        }
      })
      .catch(() => setUsingCache(true));
  }, []);

  // Internet qaytganda saqlanib qolgan (offline paytda yechilgan) natijalarni serverga yuboramiz
  useEffect(() => {
    if (!isOnline) return;
    const pending = loadPending();
    if (!pending.length) return;
    (async () => {
      const stillPending = [];
      for (const item of pending) {
        try {
          await submitQuizAttempt(item.quizId, item.answers);
        } catch {
          stillPending.push(item);
        }
      }
      savePending(stillPending);
      setPendingCount(stillPending.length);
    })();
  }, [isOnline]);

  function startQuiz(quiz) {
    setActiveQuiz(quiz);
    setAnswers({});
    setResult(null);
  }

  function choose(questionId, choiceIndex) {
    setAnswers(a => ({ ...a, [questionId]: choiceIndex }));
  }

  async function finish() {
    const questions = activeQuiz.questions || [];
    let correct = 0;
    const review = questions.map(q => {
      const chosen = answers[q.id];
      const isCorrect = chosen !== undefined && chosen === q.correct_index;
      if (isCorrect) correct += 1;
      return { question: q, chosen, isCorrect };
    });
    const scorePercent = questions.length ? Math.round((correct / questions.length) * 1000) / 10 : 0;
    setResult({ correct, total: questions.length, scorePercent, review });

    // Natijani serverga saqlashga urinamiz; muvaffaqiyatsiz bo'lsa (offlayn) navbatga qo'yamiz
    try {
      await submitQuizAttempt(activeQuiz.id, answers);
    } catch {
      const pending = loadPending();
      pending.push({ quizId: activeQuiz.id, answers, savedAt: Date.now() });
      savePending(pending);
      setPendingCount(pending.length);
    }
  }

  const allAnswered = activeQuiz && activeQuiz.questions?.length > 0 &&
    activeQuiz.questions.every(q => answers[q.id] !== undefined);

  return (
    <div>
      <h1 className="page-title">Quiz — mashq qilish</h1>
      <p className="page-sub">
        Grammatika va so'z boyligini test orqali mustahkamlang.
        {usingCache && " (offlayn — avval yuklab olingan quizlar ko'rsatilmoqda)"}
        {!isOnline && " · Internet yo'q, lekin javoblaringiz saqlanib, ulanish tiklangach yuboriladi."}
      </p>
      {pendingCount > 0 && (
        <div className="quiz-pending-banner">
          {pendingCount} ta natija hali serverga yuborilmagan — internet ulanishi bilan avtomatik yuboriladi.
        </div>
      )}

      {!activeQuiz && (
        <div className="quiz-list">
          {quizzes.length === 0 && <div className="page-sub">Hozircha quiz mavjud emas.</div>}
          {quizzes.map(q => (
            <div key={q.id} className="quiz-tile" onClick={() => startQuiz(q)}>
              <div className="quiz-tile-title">{q.title}</div>
              <div className="quiz-tile-meta">{(q.questions || []).length} ta savol</div>
            </div>
          ))}
        </div>
      )}

      {activeQuiz && !result && (
        <div className="quiz-runner">
          <button className="btn btn-outline" style={{ marginBottom: 16 }} onClick={() => setActiveQuiz(null)}>← Ro'yxatga qaytish</button>
          <div className="quiz-runner-title">{activeQuiz.title}</div>
          {(activeQuiz.questions || []).map((q, qi) => (
            <div className="quiz-question" key={q.id}>
              <div className="quiz-question-text">{qi + 1}. {q.text}</div>
              <div className="quiz-choices">
                {q.choices.map((choice, ci) => (
                  <button
                    key={ci}
                    className={"quiz-choice" + (answers[q.id] === ci ? " selected" : "")}
                    onClick={() => choose(q.id, ci)}
                  >
                    {choice}
                  </button>
                ))}
              </div>
            </div>
          ))}
          <button className="btn btn-primary" disabled={!allAnswered} onClick={finish} style={{ width: "100%", marginTop: 8 }}>
            Yakunlash va natijani ko'rish
          </button>
        </div>
      )}

      {activeQuiz && result && (
        <div className="quiz-result">
          <div className="quiz-result-score">{result.scorePercent}%</div>
          <div className="quiz-result-sub">{result.correct} / {result.total} to'g'ri javob</div>
          <div className="quiz-review">
            {result.review.map((r, i) => (
              <div key={i} className={"quiz-review-item " + (r.isCorrect ? "ok" : "bad")}>
                <div className="quiz-review-q">{r.question.text}</div>
                <div className="quiz-review-a">
                  To'g'ri javob: <strong>{r.question.choices[r.question.correct_index]}</strong>
                  {!r.isCorrect && r.chosen !== undefined && (
                    <> · Sizning javobingiz: <strong>{r.question.choices[r.chosen]}</strong></>
                  )}
                </div>
              </div>
            ))}
          </div>
          <div style={{ display: "flex", gap: 10, marginTop: 18 }}>
            <button className="btn btn-outline" style={{ flex: 1 }} onClick={() => startQuiz(activeQuiz)}>Qayta urinish</button>
            <button className="btn btn-primary" style={{ flex: 1 }} onClick={() => setActiveQuiz(null)}>Boshqa quiz</button>
          </div>
        </div>
      )}
    </div>
  );
}
