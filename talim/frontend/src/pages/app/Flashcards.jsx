import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { fetchFlashcardSession, gradeFlashcard } from "../../api/client.js";
import "./ui.css";
import "./Flashcards.css";

const SETTINGS_KEY = "st_flashcard_settings_v2";
const GRADES = [
  { q: 1, label: "Qayta", key: "1", cls: "again" },
  { q: 3, label: "Qiyin", key: "2", cls: "hard" },
  { q: 4, label: "Yaxshi", key: "3", cls: "good" },
  { q: 5, label: "Oson", key: "4", cls: "easy" },
];
const MODES = [
  { key: "flip", label: "Yodlash", hint: "Kartani ochib, o'zingizni baholang" },
  { key: "type", label: "Yozish", hint: "Tarjimani yozing, ilova tekshiradi" },
];
const DIRECTIONS = [
  { key: "en-uz", label: "EN → UZ" },
  { key: "uz-en", label: "UZ → EN" },
  { key: "mix", label: "Aralash" },
];

const loadSettings = () => {
  try { return { mode: "flip", direction: "en-uz", newCount: 10, ...JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}") }; }
  catch { return { mode: "flip", direction: "en-uz", newCount: 10 }; }
};

function normalize(s) {
  return String(s || "").toLowerCase().replace(/[’`]/g, "'").replace(/\(.*?\)/g, "").replace(/[^\p{L}\p{N}' ]/gu, " ").replace(/\s+/g, " ").trim();
}
function distance(a, b) {
  const dp = Array.from({ length: a.length + 1 }, (_, i) => [i, ...Array(b.length).fill(0)]);
  for (let j = 1; j <= b.length; j++) dp[0][j] = j;
  for (let i = 1; i <= a.length; i++)
    for (let j = 1; j <= b.length; j++)
      dp[i][j] = Math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
  return dp[a.length][b.length];
}
// "sen / siz" kabi bir nechta to'g'ri variantni hisobga oladi
function checkTyped(typed, answer) {
  const t = normalize(typed);
  if (!t) return "wrong";
  const variants = String(answer).split(/[\/,;]| yoki /).map(normalize).filter(Boolean);
  if (variants.some(v => v === t)) return "correct";
  if (variants.some(v => distance(v, t) <= Math.max(1, Math.floor(v.length / 6)))) return "close";
  return "wrong";
}

function speak(text) {
  if (!window.speechSynthesis || !text) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "en-US"; u.rate = 0.9;
  window.speechSynthesis.speak(u);
}

export default function Flashcards({ embedded = false }) {
  const [settings, setSettings] = useState(loadSettings);
  const [stats, setStats] = useState(null);
  const [queue, setQueue] = useState(null);       // sessiyadagi kartalar navbati
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const loadStats = useCallback(() => {
    setLoading(true);
    fetchFlashcardSession({ new: 0, limit: 5 })
      .then(d => setStats(d.stats))
      .catch(e => setError(e.isNetworkError ? "Internet yo'q. Flashcardlar internet qaytganda ochiladi." : e.message))
      .finally(() => setLoading(false));
  }, []);
  useEffect(loadStats, [loadStats]);

  function updateSettings(patch) {
    const next = { ...settings, ...patch };
    setSettings(next);
    try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(next)); } catch { /* */ }
  }

  async function start() {
    setError("");
    setLoading(true);
    try {
      const d = await fetchFlashcardSession({ new: settings.newCount, limit: settings.newCount + 30 });
      if (!d.cards.length) { setStats(d.stats); setError(""); setLoading(false); return; }
      const cards = d.cards.map(c => ({
        ...c,
        reverse: settings.direction === "uz-en" || (settings.direction === "mix" && Math.random() < 0.5),
      }));
      setQueue(cards);
      setSummary({ reviewed: 0, good: 0, again: 0, points: 0, total: cards.length });
    } catch (e) {
      setError(e.message || "Sessiyani boshlab bo'lmadi.");
    } finally {
      setLoading(false);
    }
  }

  function finishSession() {
    setQueue(null);
    loadStats();
  }

  if (queue) {
    return (
      <div className="ui fc">
        <Session
          queue={queue} setQueue={setQueue} mode={settings.mode}
          summary={summary} setSummary={setSummary} onDone={finishSession}
        />
      </div>
    );
  }

  const due = stats?.due_now || 0;
  const startCount = due + Math.min(settings.newCount, stats?.new || 0);

  return (
    <div className="ui fc">
      <header className="ui-head">
        <div>
          {!embedded && <h1>Flashcard</h1>}
          <p>Har kuni oz-ozdan: takrorlash vaqti kelgan kartalar va bir nechta yangi so'z. Esda qolganlari kamroq, qiyinlari tez-tez qaytadi.</p>
        </div>
      </header>

      {error && <div className="ui-alert bad">{error}</div>}

      <section className="fc-overview">
        <div className="ui-card fc-start">
          <div className="fc-deck" aria-hidden="true"><span /><span /><span /></div>
          <div className="fc-start-body">
            <h2>{startCount ? "Bugungi sessiya" : "Bugungi takrorlash tugadi"}</h2>
            <p className="ui-muted">
              {startCount
                ? <>{due > 0 && <><strong>{due}</strong> ta takrorlash · </>}<strong>{Math.min(settings.newCount, stats?.new || 0)}</strong> ta yangi karta</>
                : "Ertaga yangi takrorlashlar bo'ladi. Xohlasangiz yana yangi kartalar qo'shing."}
            </p>
            <button className="ui-btn primary fc-go" onClick={start} disabled={loading || (!startCount && !stats?.new)}>
              {loading ? "Yuklanmoqda..." : startCount ? "Boshlash" : "Yana yangi kartalar"}
            </button>
          </div>
        </div>
        <div className="fc-stats">
          <Stat label="Yangi" value={stats?.new} />
          <Stat label="O'rganilmoqda" value={stats?.learning} tone="accent" />
          <Stat label="Yodlangan" value={stats?.mastered} tone="ok" />
          <Stat label="Bugun takrorlandi" value={stats?.reviewed_today} />
        </div>
      </section>

      <section className="ui-card fc-settings">
        <div>
          <h3>Rejim</h3>
          <div className="fc-modes">
            {MODES.map(m => (
              <button key={m.key} className={"fc-mode" + (settings.mode === m.key ? " on" : "")} onClick={() => updateSettings({ mode: m.key })} aria-pressed={settings.mode === m.key}>
                <strong>{m.label}</strong><span>{m.hint}</span>
              </button>
            ))}
          </div>
        </div>
        <div>
          <h3>Yo'nalish</h3>
          <div className="ui-tabs">
            {DIRECTIONS.map(d => <button key={d.key} className={settings.direction === d.key ? "on" : ""} onClick={() => updateSettings({ direction: d.key })}>{d.label}</button>)}
          </div>
        </div>
        <div>
          <h3>Yangi kartalar</h3>
          <div className="ui-tabs">
            {[5, 10, 20].map(n => <button key={n} className={settings.newCount === n ? "on" : ""} onClick={() => updateSettings({ newCount: n })}>{n} ta</button>)}
          </div>
        </div>
      </section>
    </div>
  );
}

function Stat({ label, value, tone }) {
  return (
    <div className={"ui-card fc-stat" + (tone ? " " + tone : "")}>
      <span className="fc-stat-value">{value ?? "—"}</span>
      <span className="fc-stat-label">{label}</span>
    </div>
  );
}

function Session({ queue, setQueue, mode, summary, setSummary, onDone }) {
  const [flipped, setFlipped] = useState(false);
  const [typed, setTyped] = useState("");
  const [check, setCheck] = useState(null); // correct | close | wrong
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState("");
  const inputRef = useRef(null);
  const card = queue[0];
  const front = card ? (card.reverse ? card.back_text : card.front_text) : "";
  const back = card ? (card.reverse ? card.front_text : card.back_text) : "";
  const english = card?.front_text;
  const done = !card;

  useEffect(() => { setFlipped(false); setTyped(""); setCheck(null); if (mode === "type") setTimeout(() => inputRef.current?.focus(), 50); }, [card?.id, card?.reverse, mode]);
  useEffect(() => { if (card && !card.reverse && mode === "flip") speak(english); }, [card?.id]); // eslint-disable-line

  const grade = useCallback(async quality => {
    if (!card || busy) return;
    setBusy(true);
    try {
      const res = await gradeFlashcard(card.id, quality);
      setSummary(s => ({
        ...s, reviewed: s.reviewed + 1, points: s.points + (res.earned_points || 0),
        good: s.good + (quality >= 3 ? 1 : 0), again: s.again + (quality < 3 ? 1 : 0),
      }));
      setToast(quality < 3 ? "10 daqiqadan keyin yana chiqadi" : `Keyingi takrorlash: ${res.next_in}`);
      setTimeout(() => setToast(""), 1600);
      setQueue(q => {
        const [first, ...rest] = q;
        // "Qayta" bosilgan karta sessiya oxirida yana chiqadi (yangi intervallar bilan)
        return quality < 3 ? [...rest, { ...first, ...res, reverse: first.reverse, intervals: first.intervals }] : rest;
      });
    } catch (e) {
      setToast(e.message || "Saqlab bo'lmadi");
    } finally {
      setBusy(false);
    }
  }, [card, busy, setQueue, setSummary]);

  function submitTyped(e) {
    e.preventDefault();
    if (check) return;
    const r = checkTyped(typed, back);
    setCheck(r);
    setFlipped(true);
    if (!card.reverse) speak(english);
  }

  useEffect(() => {
    const onKey = e => {
      if (done || e.target.tagName === "INPUT") {
        if (e.target.tagName === "INPUT" && check && e.key === "Enter") { e.preventDefault(); grade(check === "correct" ? 4 : check === "close" ? 3 : 1); }
        return;
      }
      if (e.code === "Space") { e.preventDefault(); setFlipped(f => !f); }
      const g = GRADES.find(x => x.key === e.key);
      if (g && flipped) grade(g.q);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [done, flipped, grade, check]);

  if (done) {
    const acc = summary.reviewed ? Math.round((summary.good / summary.reviewed) * 100) : 0;
    return (
      <div className="fc-done ui-card">
        <div className="fc-deck done" aria-hidden="true"><span /><span /><span /></div>
        <h2>Sessiya tugadi</h2>
        <p className="ui-muted">{summary.reviewed} ta javob · {acc}% eslab qolindi{summary.points ? ` · +${summary.points} ball` : ""}</p>
        <button className="ui-btn primary" onClick={onDone}>Yakunlash</button>
      </div>
    );
  }

  const progress = Math.round((summary.reviewed / Math.max(summary.total, summary.reviewed + queue.length)) * 100);

  return (
    <div className="fc-session">
      <div className="fc-session-top">
        <button className="ui-btn sm" onClick={onDone}>Tugatish</button>
        <div className="ui-bar" style={{ flex: 1 }}><i style={{ width: `${progress}%` }} /></div>
        <span className="ui-faint">{queue.length} qoldi</span>
      </div>

      <div className={"fc-card" + (flipped ? " flipped" : "")} onClick={() => mode === "flip" && setFlipped(f => !f)}
        role={mode === "flip" ? "button" : undefined} tabIndex={mode === "flip" ? 0 : undefined}
        aria-label={mode === "flip" ? (flipped ? "Kartani yopish" : "Kartani ochish") : undefined}>
        <div className="fc-face fc-front">
          {card.is_new && <span className="ui-badge accent fc-new">Yangi</span>}
          <span className="fc-dir">{card.reverse ? "O'zbekcha" : "English"}</span>
          <span className="fc-word">{front}</span>
          {!card.reverse && <SpeakBtn text={english} />}
          {mode === "flip" && <span className="fc-hint">Ochish uchun bosing yoki Space</span>}
        </div>
        <div className="fc-face fc-back">
          <span className="fc-dir">{card.reverse ? "English" : "O'zbekcha"}</span>
          <span className="fc-word">{back}</span>
          {card.reverse && <SpeakBtn text={english} />}
          {check && (
            <span className={"fc-check " + check}>
              {check === "correct" ? "To'g'ri!" : check === "close" ? <>Deyarli: siz yozdingiz <em>{typed}</em></> : <>Siz yozdingiz: <em>{typed || "—"}</em></>}
            </span>
          )}
        </div>
      </div>

      {mode === "type" && !check && (
        <form className="fc-type" onSubmit={submitTyped}>
          <input ref={inputRef} className="ui-input" value={typed} onChange={e => setTyped(e.target.value)}
            placeholder={card.reverse ? "Inglizcha yozing..." : "O'zbekcha tarjimasini yozing..."} autoComplete="off" autoCapitalize="off" spellCheck={false} />
          <button className="ui-btn primary" type="submit">Tekshirish</button>
          <button className="ui-btn" type="button" onClick={() => { setCheck("wrong"); setFlipped(true); }}>Bilmayman</button>
        </form>
      )}

      {(flipped && (mode === "flip" || check)) && (
        <div className="fc-grades" role="group" aria-label="Qanchalik esladingiz?">
          {GRADES.map(g => {
            const suggested = check && ((check === "correct" && g.q === 4) || (check === "close" && g.q === 3) || (check === "wrong" && g.q === 1));
            return (
              <button key={g.q} className={`fc-grade ${g.cls}` + (suggested ? " suggested" : "")} onClick={() => grade(g.q)} disabled={busy}>
                <strong>{g.label}</strong>
                <span>{card.intervals?.[String(g.q)] || ""}</span>
                <kbd>{g.key}</kbd>
              </button>
            );
          })}
        </div>
      )}
      <p className="fc-toast" aria-live="polite">{toast}</p>
    </div>
  );
}

function SpeakBtn({ text }) {
  return (
    <button className="fc-speak" onClick={e => { e.stopPropagation(); speak(text); }} aria-label="Talaffuzni eshitish">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M11 5 6 9H2v6h4l5 4V5Z" /><path d="M15.5 8.5a5 5 0 0 1 0 7M19 5a10 10 0 0 1 0 14" /></svg>
    </button>
  );
}
