import React, { useEffect, useRef, useState } from "react";
import { fetchSubjects, fetchAvatars, createSession, sendAvatarMessage, endSession } from "../../api/client.js";
import "./Chat.css";

const SpeechRecognitionApi = typeof window !== "undefined"
  ? (window.SpeechRecognition || window.webkitSpeechRecognition)
  : null;

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [avatar, setAvatar] = useState(null);
  const [levelLabel, setLevelLabel] = useState("B1 daraja");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [orbState, setOrbState] = useState("idle"); // idle | listening | thinking | speaking
  const sessionRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    (async () => {
      try {
        const [subjects, avatars] = await Promise.all([fetchSubjects(), fetchAvatars()]);
        const english = (subjects || []).find(s => s.code === "english");
        const chosen = (avatars || [])[0];
        if (!english) throw new Error("Ingliz tili fani topilmadi.");
        setAvatar(chosen || null);
        const session = await createSession(english.id, chosen?.id || null);
        sessionRef.current = session.id;
        if (session.turns?.length) {
          setMessages(session.turns.map(t => ({ id: t.id, text: t.text, mine: t.speaker === "user" })));
        }
      } catch (e) {
        setError(e.message || "Avatar sessiyasini boshlashda xatolik.");
      } finally { setLoading(false); }
    })();
    return () => {
      recognitionRef.current?.stop();
      window.speechSynthesis?.cancel();
      if (sessionRef.current) endSession(sessionRef.current).catch(() => {});
    };
  }, []);

  async function send(overrideText, { speak = false } = {}) {
    const text = (overrideText ?? input).trim();
    if (!text || !sessionRef.current || sending) return;
    setInput("");
    setError("");
    setMessages(m => [...m, { id: `u-${Date.now()}`, text, mine: true }]);
    setSending(true);
    setOrbState("thinking");
    try {
      const res = await sendAvatarMessage(sessionRef.current, text);
      setMessages(m => [...m, { id: res.reply.id, text: res.reply.text, mine: false }]);
      if (speak) speakReply(res.reply.text); else setOrbState("idle");
    } catch (e) {
      setError(e.message || "Avatar javob bera olmadi.");
      setOrbState("idle");
    } finally { setSending(false); }
  }

  function speakReply(text) {
    if (!window.speechSynthesis) { setOrbState("idle"); return; }
    setOrbState("speaking");
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = "en-US";
    utter.onend = () => setOrbState("idle");
    utter.onerror = () => setOrbState("idle");
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utter);
  }

  function toggleListening() {
    if (!SpeechRecognitionApi) {
      alert("Bu brauzer ovozli kiritishni qo'llab-quvvatlamaydi. Matn bilan yozishingiz mumkin.");
      return;
    }
    if (orbState === "listening") {
      recognitionRef.current?.stop();
      return;
    }
    window.speechSynthesis?.cancel();
    const rec = new SpeechRecognitionApi();
    rec.lang = "en-US";
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    rec.onstart = () => setOrbState("listening");
    rec.onerror = () => setOrbState("idle");
    rec.onend = () => setOrbState(s => (s === "listening" ? "idle" : s));
    rec.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      send(transcript, { speak: true });
    };
    recognitionRef.current = rec;
    rec.start();
  }

  return (
    <div>
      <h1 className="page-title" style={{ marginBottom: 8 }}>Avatar bilan suhbat — Ingliz tili</h1>
      <p className="page-sub">Real backend sessiyasi va AI repetitor javobi</p>
      {error && <div className="math-feedback wrong" style={{ marginBottom: 14 }}>{error}</div>}
      <div className="chat-grid">
        <div className="avatar-card">
          <div className="avatar-orb-frame">
            <div className={"avatar-orb " + orbState} />
          </div>
          <div style={{ fontWeight: 700, fontSize: 14.5 }}>{avatar?.name || "Avatar"}</div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 12 }}>{levelLabel}</div>
          <div className="avatar-orb-status">
            {orbState === "listening" && "Tinglayapman..."}
            {orbState === "thinking" && "O'ylayapman..."}
            {orbState === "speaking" && "Gapiryapman..."}
            {orbState === "idle" && "Tayyor"}
          </div>
          <button className={"avatar-mic-btn" + (orbState === "listening" ? " active" : "")} onClick={toggleListening} disabled={loading}>
            <VoiceIcon /> {orbState === "listening" ? "To'xtatish" : "Ovoz bilan gapirish"}
          </button>
        </div>
        <div className="chat-panel">
          <div className="chat-messages">
            {loading && <div className="page-sub">Sessiya boshlanmoqda...</div>}
            {!loading && !messages.length && <div className="page-sub">Salom! Ingliz tilida gaplashishni boshlang 👋</div>}
            {messages.map(m => (
              <div key={m.id} className={"msg-row " + (m.mine ? "mine" : "theirs")}>
                <div className={"msg-bubble " + (m.mine ? "mine" : "theirs")}>{m.text}</div>
              </div>
            ))}
          </div>
          <div className="chat-input-row">
            <input className="input" placeholder="Ingliz tilida xabar yozing..." value={input} onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && send()} disabled={loading || sending} />
            <button className="btn btn-primary" onClick={() => send()} disabled={loading || sending}>{sending ? "Javob tayyorlanmoqda..." : "Yuborish"}</button>
          </div>
        </div>
      </div>
    </div>
  );
}

function VoiceIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ verticalAlign: "-2px", marginRight: 4 }}>
      <path d="M12 15a3 3 0 003-3V6a3 3 0 10-6 0v6a3 3 0 003 3z" stroke="currentColor" strokeWidth="1.8" />
      <path d="M19 11a7 7 0 01-14 0M12 18v3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}
