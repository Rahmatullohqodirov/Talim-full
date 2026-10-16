import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { addWordToLearning, searchDictionary } from "../api/client.js";
import { searchWordOnline } from "../api/dictionaryApi.js";
import "./app/ui.css";
import "./Dictionary.css";

const RECENT_KEY = "st_dict_recent";
const POS_UZ = {
  noun: "ot", verb: "fe'l", adjective: "sifat", adverb: "ravish", preposition: "predlog", pronoun: "olmosh",
  determiner: "aniqlovchi", conjunction: "bog'lovchi", number: "son", interjection: "undov",
};
const STATUS = { new: null, learning: "O'rganilmoqda", mastered: "O'zlashtirilgan" };

function speak(text) {
  if (!window.speechSynthesis || !text) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "en-US"; u.rate = 0.9;
  window.speechSynthesis.speak(u);
}
const loadRecent = () => { try { return JSON.parse(localStorage.getItem(RECENT_KEY) || "[]"); } catch { return []; } };

export default function Dictionary() {
  const [q, setQ] = useState("");
  const [data, setData] = useState(null);
  const [selected, setSelected] = useState(null);
  const [online, setOnline] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [recent, setRecent] = useState(loadRecent);
  const timer = useRef(null);

  useEffect(() => { searchDictionary("").then(setData).catch(() => {}); }, []);

  function run(text) {
    const query = text.trim();
    setError(""); setOnline(null);
    if (!query) { searchDictionary("").then(d => { setData(d); setSelected(null); }).catch(() => {}); return; }
    setLoading(true);
    searchDictionary(query)
      .then(d => {
        setData(d);
        const exact = d.results.find(w => w.headword.toLowerCase() === query.toLowerCase()) || d.results[0] || null;
        setSelected(exact);
        if (!d.results.length && /^[a-z\s'-]+$/i.test(query)) {
          searchWordOnline(query).then(setOnline).catch(() => setOnline(false));
        }
      })
      .catch(e => setError(e.isNetworkError ? "Internet yo'q." : e.message))
      .finally(() => setLoading(false));
  }

  function onChange(v) {
    setQ(v);
    clearTimeout(timer.current);
    timer.current = setTimeout(() => run(v), 300);
  }

  function pick(w) {
    setSelected(w);
    speak(w.headword);
    const next = [w.headword, ...recent.filter(r => r !== w.headword)].slice(0, 8);
    setRecent(next);
    try { localStorage.setItem(RECENT_KEY, JSON.stringify(next)); } catch { /* */ }
  }

  async function addToLearning(w) {
    try {
      const updated = await addWordToLearning(w.id);
      setSelected(updated);
      setData(d => d && ({ ...d, results: d.results.map(x => (x.id === w.id ? updated : x)),
        word_of_day: d.word_of_day?.id === w.id ? updated : d.word_of_day }));
    } catch (e) { setError(e.message || "Qo'shib bo'lmadi."); }
  }

  const results = data?.results || [];
  const showWord = selected || (!q && data?.word_of_day);

  return (
    <div className="ui dict">
      <header className="ui-head">
        <div>
          <h1>Lug'at</h1>
          <p>Inglizcha yoki o'zbekcha so'z yozing. Tarjima, misol va talaffuz. Kerakli so'zni o'rganish ro'yxatiga qo'shing.</p>
        </div>
      </header>

      <div className="dict-search" role="search">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>
        <input value={q} onChange={e => onChange(e.target.value)} placeholder="Masalan: journey yoki sayohat" aria-label="So'z qidirish" autoFocus autoCapitalize="off" spellCheck={false} />
        {q && <button className="dict-clear" onClick={() => onChange("")} aria-label="Tozalash">×</button>}
      </div>

      {!q && recent.length > 0 && (
        <div className="ui-chips dict-recent">
          <span className="ui-faint">Oxirgi:</span>
          {recent.map(r => <button key={r} className="ui-chip" onClick={() => onChange(r)}>{r}</button>)}
        </div>
      )}
      {error && <div className="ui-alert bad">{error}</div>}

      <div className={"dict-body" + (q ? " searching" : "")}>
        {q && (
          <div className="ui-card dict-list" aria-busy={loading}>
            {loading && !results.length && <p className="ui-muted">Qidirilmoqda...</p>}
            {!loading && !results.length && (
              online ? (
                <div className="dict-online">
                  <p className="ui-faint">Platforma lug'atida yo'q, internetdan topildi:</p>
                  <p><strong>{online.en}</strong> {online.phonetic && <span className="ui-faint">{online.phonetic}</span>}</p>
                  <p>{online.uz}</p>
                </div>
              ) : <p className="ui-muted">"{q}" topilmadi. Boshqacha yozib ko'ring.</p>
            )}
            <ul>
              {results.map(w => (
                <li key={w.id}>
                  <button className={"dict-item" + (selected?.id === w.id ? " on" : "")} onClick={() => pick(w)}>
                    <span className="dict-item-head">{w.headword}</span>
                    <span className="dict-item-uz">{w.uz || "—"}</span>
                    <span className="ui-badge">{w.cefr}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {showWord && (
          <article className="ui-card dict-word">
            {!q && <p className="dict-kicker">Kun so'zi</p>}
            <div className="dict-word-top">
              <h2>{showWord.headword}</h2>
              <button className="dict-speak" onClick={() => speak(showWord.headword)} aria-label="Talaffuz">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M11 5 6 9H2v6h4l5 4V5Z" /><path d="M15.5 8.5a5 5 0 0 1 0 7M19 5a10 10 0 0 1 0 14" /></svg>
              </button>
            </div>
            <div className="dict-meta">
              <span className="ui-badge">{POS_UZ[showWord.pos] || showWord.pos}</span>
              <span className="ui-badge accent">{showWord.cefr}</span>
              {STATUS[showWord.status] && <span className={"ui-badge " + (showWord.status === "mastered" ? "ok" : "pen")}>{STATUS[showWord.status]}</span>}
            </div>
            <p className="dict-uz">{showWord.uz || <span className="ui-faint">Tarjima hali yo'q</span>}</p>
            {showWord.example && (
              <blockquote className="dict-example">
                <p>{showWord.example}</p>
                {showWord.example_uz && <p className="ui-faint">{showWord.example_uz}</p>}
              </blockquote>
            )}
            <div className="dict-actions">
              {showWord.status === "new"
                ? <button className="ui-btn primary" onClick={() => addToLearning(showWord)}>O'rganishga qo'shish</button>
                : <Link className="ui-btn" to={`/app/vocabulary/${showWord.cefr}?mode=learn`}>Mashq qilish</Link>}
              <Link className="ui-btn" to={`/app/vocabulary/${showWord.cefr}?mode=list`}>{showWord.cefr} so'zlari</Link>
            </div>
          </article>
        )}
      </div>
    </div>
  );
}
