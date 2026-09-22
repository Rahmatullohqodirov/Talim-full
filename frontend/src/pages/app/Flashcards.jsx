import React, { useEffect, useState } from "react";
import { fetchDueFlashcards, gradeFlashcard } from "../../api/client.js";
import "./Flashcards.css";

export default function Flashcards() {
  const [cards, setCards] = useState([]);
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await fetchDueFlashcards();
      setCards(Array.isArray(data) ? data : (data?.results || []));
      setIndex(0);
      setFlipped(false);
    } catch (e) {
      setError(e.message || "Flashcardlarni yuklab bo'lmadi.");
    } finally { setLoading(false); }
  }

  useEffect(() => { load(); }, []);

  const card = cards[index];

  async function next(quality) {
    if (!card) return;
    try {
      await gradeFlashcard(card.id, quality);
      const remaining = cards.filter((_, i) => i !== index);
      setCards(remaining);
      setIndex(i => Math.min(i, Math.max(remaining.length - 1, 0)));
      setFlipped(false);
    } catch (e) {
      setError(e.message || "Bahoni saqlab bo'lmadi.");
    }
  }

  return (
    <div>
      <h1 className="page-title" style={{ marginBottom: 20 }}>Flashcard (Spaced Repetition)</h1>
      {loading && <div className="page-sub">Bugungi kartalar yuklanmoqda...</div>}
      {error && <div className="math-feedback wrong">{error}</div>}
      {!loading && !card && !error && (
        <div className="flash-wrap">
          <div className="flash-card">Bugun uchun yangi karta qolmadi 🎉</div>
          <div className="flash-hint">Keyingi review vaqti kelganda kartalar yana chiqadi.</div>
        </div>
      )}
      {card && (
        <div className="flash-wrap">
          <div className="flash-card" onClick={() => setFlipped(f => !f)}>{flipped ? card.back_text : card.front_text}</div>
          <div className="flash-hint">Kartani ag'darish uchun bosing · {index + 1} / {cards.length}</div>
          <div className="flash-actions">
            <button className="flash-btn" style={{ background: "oklch(0.6 0.18 25)" }} onClick={() => next(1)}>Bilmadim</button>
            <button className="flash-btn" style={{ background: "oklch(0.7 0.15 85)" }} onClick={() => next(3)}>Qiynaldim</button>
            <button className="flash-btn" style={{ background: "oklch(0.6 0.15 155)" }} onClick={() => next(5)}>Bilaman</button>
          </div>
        </div>
      )}
    </div>
  );
}
