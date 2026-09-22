import React, { useEffect, useRef, useState } from "react";
import { aiChatMessages as initialMessages } from "../../data/mockData.js";
import { createChatThread, sendChatMessage } from "../../api/client.js";
import "./AIChat.css";

const SpeechRecognitionApi = typeof window !== "undefined"
  ? (window.SpeechRecognition || window.webkitSpeechRecognition)
  : null;

export default function AIChat() {
  const [messages, setMessages] = useState(initialMessages);
  const [input, setInput] = useState("");
  const [threadId, setThreadId] = useState(null);
  const [sending, setSending] = useState(false);
  const [voiceMode, setVoiceMode] = useState(false);
  const [orbState, setOrbState] = useState("idle"); // idle | listening | thinking | speaking
  const recognitionRef = useRef(null);

  async function ensureThread() {
    if (threadId) return threadId;
    try {
      const thread = await createChatThread(null);
      setThreadId(thread.id);
      return thread.id;
    } catch (e) {
      return null;
    }
  }

  async function send(overrideText, { speak = false } = {}) {
    const text = (overrideText ?? input).trim();
    if (!text || sending) return;
    setInput("");
    setMessages(m => [...m, { id: Date.now(), role: "user", text }]);
    setSending(true);
    setOrbState("thinking");
    const tid = await ensureThread();
    let replyText = null;
    if (tid) {
      try {
        const reply = await sendChatMessage(tid, text);
        replyText = reply.content;
      } catch (e) { /* fall through to demo reply */ }
    }
    if (replyText === null) {
      await new Promise(r => setTimeout(r, 500));
      replyText = "(Demo) Backend ulanmagan — real javob uchun API'ni ishga tushiring.";
    }
    setMessages(m => [...m, { id: Date.now() + 1, role: "assistant", text: replyText }]);
    setSending(false);
    if (speak) speakReply(replyText); else setOrbState("idle");
  }

  function speakReply(text) {
    if (!window.speechSynthesis) { setOrbState("idle"); return; }
    setOrbState("speaking");
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = "uz-UZ";
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
    rec.lang = "uz-UZ";
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

  function openVoiceMode() {
    setVoiceMode(true);
    setOrbState("idle");
  }

  function closeVoiceMode() {
    recognitionRef.current?.stop();
    window.speechSynthesis?.cancel();
    setVoiceMode(false);
    setOrbState("idle");
  }

  useEffect(() => () => { window.speechSynthesis?.cancel(); recognitionRef.current?.stop(); }, []);

  return (
    <div>
      <h1 className="page-title">AI Chat repetitor</h1>
      <p className="page-sub">Har qanday savol bering — grammatika, masala yechimi yoki maslahat</p>
      <div className="ai-chat-panel">
        <div className="ai-chat-messages">
          {messages.map(m => <div key={m.id} className={"ai-msg " + m.role}>{m.text}</div>)}
        </div>
        <div className="ai-chat-input-row">
          <button className="ai-voice-toggle" onClick={openVoiceMode} title="Ovozli rejim">
            <VoiceIcon />
          </button>
          <input className="input" placeholder="Savolingizni yozing..." value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && send()} />
          <button className="btn btn-primary" onClick={() => send()} disabled={sending}>{sending ? "..." : "Yuborish"}</button>
        </div>
      </div>

      {voiceMode && (
        <div className="voice-overlay">
          <button className="voice-overlay-close" onClick={closeVoiceMode} aria-label="Yopish">✕</button>
          <div className="voice-orb-wrap">
            <div className={"voice-orb " + orbState} />
            <div className="voice-orb-label">
              {orbState === "listening" && "Tinglayapman..."}
              {orbState === "thinking" && "O'ylayapman..."}
              {orbState === "speaking" && "Javob bermoqda..."}
              {orbState === "idle" && "Gapirish uchun mikrofonni bosing"}
            </div>
          </div>
          <div className="voice-bottom-bar">
            <button className="voice-bar-icon" title="Qo'shish">+</button>
            <input
              className="voice-bar-input"
              placeholder="Yozing..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && send(undefined, { speak: true })}
            />
            <button
              className={"voice-bar-mic" + (orbState === "listening" ? " active" : "")}
              onClick={toggleListening}
              title="Mikrofon"
            >
              <VoiceIcon />
            </button>
            <button className="voice-bar-close" onClick={closeVoiceMode} aria-label="Yopish">✕</button>
          </div>
        </div>
      )}
    </div>
  );
}

function VoiceIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 15a3 3 0 003-3V6a3 3 0 10-6 0v6a3 3 0 003 3z" stroke="currentColor" strokeWidth="1.8" />
      <path d="M19 11a7 7 0 01-14 0M12 18v3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}
