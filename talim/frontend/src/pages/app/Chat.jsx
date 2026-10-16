import React, { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { createSession, fetchAvatars, fetchScenarios, fetchSubjects, sendAvatarMessage, updateProfile } from "../../api/client.js";
import "./ui.css";
import "./Chat.css";

const SpeechRecognitionApi = typeof window !== "undefined" ? (window.SpeechRecognition || window.webkitSpeechRecognition) : null;
const LANGS = {
  english: { label: "Ingliz tili", speech: { american: "en-US", british: "en-GB" }, hello: "Hi! I'm ready when you are." },
  german: { label: "Nemis tili", speech: { default: "de-DE" }, hello: "Hallo! Ich bin bereit." },
  russian: { label: "Rus tili", speech: { default: "ru-RU" }, hello: "Привет! Я готов(а) поговорить." },
  turkish: { label: "Turk tili", speech: { default: "tr-TR" }, hello: "Merhaba! Hazırım." },
};
const DEFAULT_SCENARIOS = [{ key: "free", label: "Erkin suhbat" }];
const store = {
  get: (k, d) => { try { return localStorage.getItem(k) ?? d; } catch { return d; } },
  set: (k, v) => { try { localStorage.setItem(k, v); } catch { /* */ } },
};

export default function Chat() {
  const [subjects, setSubjects] = useState([]);
  const [subjectCode, setSubjectCode] = useState(() => store.get("st_avatar_subject", "english"));
  const [avatars, setAvatars] = useState([]);
  const [avatar, setAvatar] = useState(null);
  const [scenarios, setScenarios] = useState(DEFAULT_SCENARIOS);
  const [scenario, setScenario] = useState(() => store.get("st_avatar_scenario", "free"));
  const [accent, setAccent] = useState(() => store.get("st_accent", "american"));
  const [session, setSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [state, setState] = useState("idle"); // idle | listening | thinking | speaking
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const recognitionRef = useRef(null);
  const audioRef = useRef(null);
  const listRef = useRef(null);

  const lang = LANGS[subjectCode] || LANGS.english;
  const speechLang = lang.speech[accent] || lang.speech.default || lang.speech.american;

  useEffect(() => {
    Promise.all([fetchSubjects(), fetchAvatars(), fetchScenarios().catch(() => DEFAULT_SCENARIOS)])
      .then(([subs, avs, scs]) => {
        const list = (subs?.results || subs || []).filter(s => LANGS[s.code]);
        setSubjects(list);
        const av = avs?.results || avs || [];
        setAvatars(av);
        setAvatar(av.find(a => a.id === store.get("st_avatar_id", "")) || av.find(a => !a.is_premium_only) || av[0] || null);
        setScenarios(scs?.length ? scs : DEFAULT_SCENARIOS);
        if (!list.some(s => s.code === subjectCode) && list[0]) setSubjectCode(list[0].code);
      })
      .catch(e => { setError(e.isNetworkError ? "Server bilan aloqa yo'q." : e.message); setLoading(false); });
    return () => { recognitionRef.current?.abort?.(); audioRef.current?.pause(); window.speechSynthesis?.cancel(); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const start = useCallback(async (fresh = false) => {
    const subject = subjects.find(s => s.code === subjectCode);
    if (!subject || !avatar) return;
    setLoading(true); setError("");
    try {
      const s = await createSession(subject.id, avatar.id, scenario, fresh);
      setSession(s);
      setMessages((s.turns || []).map(t => ({ id: t.id, text: t.text, mine: t.speaker === "user", feedback: t.feedback })));
    } catch (e) {
      setSession(null);
      setError(e.data?.code === "premium_required" ? "Bu avatar faqat Premium obunada. Boshqa avatarni tanlang." : e.message || "Suhbatni boshlab bo'lmadi.");
    } finally {
      setLoading(false);
    }
  }, [subjects, subjectCode, avatar, scenario]);

  useEffect(() => { if (subjects.length && avatar) start(false); }, [subjects, subjectCode, avatar, scenario]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" }); }, [messages, state]);

  function choose(kind, value) {
    if (kind === "avatar") {
      setAvatar(value); store.set("st_avatar_id", value.id);
      updateProfile({ avatar_preference: value.id }).catch(() => {});
    }
    if (kind === "subject") { setSubjectCode(value); store.set("st_avatar_subject", value); }
    if (kind === "scenario") { setScenario(value); store.set("st_avatar_scenario", value); }
    if (kind === "accent") { setAccent(value); store.set("st_accent", value); }
  }

  function speakBrowser(text) {
    if (!window.speechSynthesis) { setState("idle"); return; }
    const u = new SpeechSynthesisUtterance(text);
    u.lang = speechLang;
    const voices = window.speechSynthesis.getVoices();
    const female = avatar?.gender === "female";
    const match = voices.filter(v => v.lang?.toLowerCase().startsWith(speechLang.slice(0, 2).toLowerCase()));
    const byGender = match.find(v => (female ? /female|woman|zira|samantha|jenny|sonia|aria/i : /male|man|david|guy|ryan|daniel/i).test(v.name));
    if (byGender || match[0]) u.voice = byGender || match[0];
    u.onend = u.onerror = () => setState("idle");
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
  }

  function play(text, b64) {
    setState("speaking");
    if (b64) {
      const a = new Audio(`data:audio/mpeg;base64,${b64}`);
      audioRef.current = a;
      a.onended = () => setState("idle");
      a.onerror = () => speakBrowser(text);
      a.play().catch(() => speakBrowser(text));
    } else speakBrowser(text);
  }

  async function send(textArg, { voice = false } = {}) {
    const text = (textArg ?? input).trim();
    if (!text || !session || state === "thinking") return;
    setInput(""); setError("");
    setMessages(m => [...m, { id: "u" + Date.now(), text, mine: true }]);
    setState("thinking");
    try {
      const res = await sendAvatarMessage(session.id, text, accent);
      setMessages(m => [...m, { id: res.reply.id, text: res.reply.text, mine: false, feedback: res.reply.feedback }]);
      if (voice || res.audio_base64) play(res.reply.text, res.audio_base64); else setState("idle");
    } catch (e) {
      setState("idle");
      setError(e.isNetworkError ? "Internet bilan aloqa yo'q." : e.message || "Avatar javob bera olmadi.");
    }
  }

  function toggleMic() {
    if (state === "listening") { recognitionRef.current?.stop(); return; }
    if (state === "speaking") { audioRef.current?.pause(); window.speechSynthesis?.cancel(); setState("idle"); return; }
    if (!SpeechRecognitionApi) { setError("Bu brauzer ovozni taniy olmaydi. Chrome yoki Edge'da oching yoki yozib yuboring."); return; }
    setError("");
    const rec = new SpeechRecognitionApi();
    rec.lang = speechLang;
    rec.interimResults = false;
    rec.onstart = () => setState("listening");
    rec.onerror = ev => { setState("idle"); if (ev.error === "not-allowed") setError("Mikrofonga ruxsat berilmadi."); else if (ev.error === "no-speech") setError("Ovoz eshitilmadi, yana urinib ko'ring."); };
    rec.onend = () => setState(s => (s === "listening" ? "idle" : s));
    rec.onresult = e => send(e.results[0][0].transcript, { voice: true });
    recognitionRef.current = rec;
    rec.start();
  }

  const label = { idle: "Gapirish uchun bosing", listening: "Tinglayapman...", thinking: "O'ylayapman...", speaking: "Gapiryapti · to'xtatish" }[state];
  const scenarioLabel = scenarios.find(s => s.key === scenario)?.label || "Erkin suhbat";

  return (
    <div className="ui av">
      <header className="ui-head">
        <div>
          <h1>Avatar bilan suhbat</h1>
          <p>Jonli suhbat mashqi: vaziyatni tanlang va avatar bilan o'rganayotgan tilingizda gaplashing. Xatolar alohida izohda ko'rsatiladi.</p>
        </div>
        {subjects.length > 1 && (
          <div className="ui-tabs" aria-label="Til">
            {subjects.map(s => <button key={s.code} className={subjectCode === s.code ? "on" : ""} onClick={() => choose("subject", s.code)}>{LANGS[s.code].label}</button>)}
          </div>
        )}
      </header>

      <div className="ui-chips av-scenarios" aria-label="Vaziyat">
        {scenarios.map(s => <button key={s.key} className={"ui-chip" + (scenario === s.key ? " on" : "")} onClick={() => choose("scenario", s.key)}>{s.label}</button>)}
      </div>

      {error && <div className="ui-alert bad">{error}</div>}

      <div className="av-grid">
        <section className="av-stage">
          <div className={"av-portrait " + state}>
            <span className="av-ring r1" /><span className="av-ring r2" />
            {avatar?.preview_image_url ? <img src={avatar.preview_image_url} alt="" /> : <span className="av-initial">{avatar?.name?.[0] || "A"}</span>}
          </div>
          <h2 className="av-name">{avatar?.name || "Avatar"}</h2>
          <p className="av-role">{scenarioLabel} · {lang.label}</p>
          {subjectCode === "english" && (
            <div className="ui-tabs av-accent" aria-label="Aksent">
              <button className={accent === "american" ? "on" : ""} onClick={() => choose("accent", "american")}>Amerika</button>
              <button className={accent === "british" ? "on" : ""} onClick={() => choose("accent", "british")}>Britaniya</button>
            </div>
          )}
          <button className={"av-mic " + state} onClick={toggleMic} disabled={loading || !session || state === "thinking"} aria-label={label}>
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" aria-hidden="true"><rect x="9" y="3" width="6" height="12" rx="3" /><path d="M19 11a7 7 0 0 1-14 0M12 18v3" /></svg>
          </button>
          <p className="av-state" aria-live="polite">{label}</p>
          {avatars.length > 1 && (
            <div className="av-picker" aria-label="Avatar tanlash">
              {avatars.map(a => (
                <button key={a.id} className={"av-pick" + (avatar?.id === a.id ? " on" : "") + (a.is_premium_only ? " premium" : "")}
                  onClick={() => choose("avatar", a)} title={a.name + (a.is_premium_only ? " (Premium)" : "")} aria-pressed={avatar?.id === a.id}>
                  {a.preview_image_url ? <img src={a.preview_image_url} alt={a.name} /> : a.name[0]}
                  {a.is_premium_only && <span className="av-lock" aria-hidden="true">★</span>}
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="ui-card av-chat">
          <div className="av-chat-head">
            <span className="ui-faint">{messages.length ? `${Math.ceil(messages.length / 2)} ta almashinuv` : "Yangi suhbat"}</span>
            <button className="ui-btn sm" onClick={() => start(true)} disabled={loading}>Yangi suhbat</button>
          </div>
          <div className="av-messages" ref={listRef}>
            {loading && <p className="ui-muted">Suhbat tayyorlanmoqda...</p>}
            {!loading && !messages.length && (
              <div className="av-empty">
                <p><strong>{avatar?.name}</strong> sizni kutyapti.</p>
                <p className="ui-muted">Mikrofonni bosib gapiring yoki pastda yozing. Masalan: <em>"{lang.hello}"</em></p>
              </div>
            )}
            {messages.map(m => (
              <div key={m.id} className={"av-msg " + (m.mine ? "me" : "them")}>
                <div className="av-bubble">{m.text}</div>
                {!m.mine && m.feedback && <div className="av-note"><b>Tuzatish</b>{m.feedback}</div>}
              </div>
            ))}
            {state === "thinking" && <div className="av-msg them"><div className="av-bubble av-typing"><i /><i /><i /></div></div>}
          </div>
          <form className="av-input" onSubmit={e => { e.preventDefault(); send(); }}>
            <input className="ui-input" placeholder={`${lang.label}da yozing...`} value={input} onChange={e => setInput(e.target.value)} disabled={loading || !session} />
            <button className="ui-btn primary" disabled={!input.trim() || state === "thinking"}>Yuborish</button>
          </form>
        </section>
      </div>
      <p className="ui-faint av-foot">Darsga o'xshash tushuntirish kerak bo'lsa, <Link to="/app/ai-chat">AI Ustoz</Link>dan so'rang.</p>
    </div>
  );
}
