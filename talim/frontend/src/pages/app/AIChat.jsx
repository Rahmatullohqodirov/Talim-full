import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  clearTutorMemories,
  createChatThread,
  deleteChatThread,
  deleteTutorMemory,
  fetchChatThread,
  fetchChatThreads,
  fetchSubjects,
  fetchTutorMemories,
  fetchTutorStatus,
  sendChatMessage,
  sendSpeakingAudio,
  sendVoiceAudio,
} from "../../api/client.js";
import { useSearchParams } from "react-router-dom";
import { useOnlineStatus } from "../../hooks/useOnlineStatus.js";
import RichText from "./RichText.jsx";
import "./AIChat.css";

const SUBJECTS = [
  { code: "english", label: "Ingliz tili", speech: "en-US" },
  { code: "german", label: "Nemis tili", speech: "de-DE" },
  { code: "russian", label: "Rus tili", speech: "ru-RU" },
  { code: "turkish", label: "Turk tili", speech: "tr-TR" },
  { code: "uzbek", label: "O'zbek tili", speech: "uz-UZ" },
  { code: "math", label: "Matematika", speech: null },
];
const subjectInfo = code => SUBJECTS.find(s => s.code === code);

const STARTERS = [
  { title: "Dars o'tish", text: "Menga darajamga mos dars o'ting." },
  { title: "Darajamni aniqlash", text: "Darajamni aniqlash uchun qisqa test o'tkazing." },
  { title: "Yozganimni tekshirish", text: "Men kichik matn yozdim, xatolarimni tekshirib bering:\n\n" },
  { title: "Haftalik reja tuzish", text: "Menga shu hafta uchun haftalik o'quv reja tuzib bering." },
];

const TOOL_LABELS = {
  get_user_level: "Daraja tekshirildi",
  update_user_level: "Daraja saqlandi",
  create_lesson_plan: "Dars rejasi tuzildi",
  save_test_result: "Natija saqlandi",
  get_statistics: "Statistika olindi",
  get_vocabulary: "Lug'atdan so'zlar olindi",
  get_subscription_status: "Obuna tekshirildi",
  escalate_to_admin: "Adminga murojaat yuborildi",
  remember_about_student: "Eslab qolindi",
  forget_about_student: "Xotiradan o'chirildi",
  start_lesson: "Dars rejasi tuzildi",
  update_lesson_progress: "Javob baholandi",
  finish_lesson: "Dars yakunlandi",
  create_study_plan: "O'quv reja saqlandi",
  mark_plan_item: "Reja vazifasi belgilandi",
};

const SpeechRecognitionApi = typeof window !== "undefined"
  ? (window.SpeechRecognition || window.webkitSpeechRecognition)
  : null;

function groupThreads(threads) {
  const today = new Date().toDateString();
  const groups = { today: [], earlier: [] };
  threads.forEach(t => (new Date(t.updated_at).toDateString() === today ? groups.today : groups.earlier).push(t));
  return groups;
}

export default function AIChat() {
  const { isOnline } = useOnlineStatus();
  const [available, setAvailable] = useState(SUBJECTS.filter(s => s.code !== "uzbek"));
  const [threads, setThreads] = useState([]);
  const [thread, setThread] = useState(null); // {id, title, subject_code}
  const [messages, setMessages] = useState([]);
  const [subject, setSubject] = useState("english");
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [failed, setFailed] = useState(null); // {text, error}
  const [railOpen, setRailOpen] = useState(false);
  const [voiceOpen, setVoiceOpen] = useState(false);
  const [memoryOpen, setMemoryOpen] = useState(false);
  const [loadingThread, setLoadingThread] = useState(false);
  const [status, setStatus] = useState(null);
  const [searchParams, setSearchParams] = useSearchParams();
  const listRef = useRef(null);
  const inputRef = useRef(null);
  const autoSent = useRef(false);

  useEffect(() => { fetchTutorStatus().then(setStatus).catch(() => {}); }, []);

  // Dashboard'dan kelgan so'rov (?q=...) avtomatik yuboriladi
  useEffect(() => {
    const q = searchParams.get("q");
    if (q && !autoSent.current && isOnline) {
      autoSent.current = true;
      setSearchParams({}, { replace: true });
      send(q);
    }
  }, [searchParams, isOnline]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    fetchSubjects()
      .then(list => {
        const codes = new Set((list?.results || list || []).map(s => s.code));
        if (codes.size) setAvailable(SUBJECTS.filter(s => codes.has(s.code)));
      })
      .catch(() => {});
    refreshThreads();
  }, []);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, sending]);

  function refreshThreads() {
    return fetchChatThreads()
      .then(list => setThreads(list?.results || list || []))
      .catch(() => {});
  }

  async function openThread(t) {
    setRailOpen(false);
    setFailed(null);
    setLoadingThread(true);
    try {
      const full = await fetchChatThread(t.id);
      setThread(full);
      setMessages(full.messages || []);
      if (full.subject_code) setSubject(full.subject_code);
    } catch {
      setFailed({ error: "Suhbatni ochib bo'lmadi. Internetni tekshirib, qayta urinib ko'ring." });
    } finally {
      setLoadingThread(false);
    }
  }

  function newChat() {
    setThread(null);
    setMessages([]);
    setFailed(null);
    setRailOpen(false);
    setTimeout(() => inputRef.current?.focus(), 0);
  }

  async function removeThread(t, e) {
    e.stopPropagation();
    if (!window.confirm(`"${t.title || "Yangi suhbat"}" o'chirilsinmi?`)) return;
    try {
      await deleteChatThread(t.id);
      setThreads(list => list.filter(x => x.id !== t.id));
      if (thread?.id === t.id) newChat();
    } catch { /* tarmoq xatosi — ro'yxat o'zgarmaydi */ }
  }

  const ensureThread = useCallback(async (subjectCode = subject) => {
    if (thread) return thread;
    const created = await createChatThread(subjectCode);
    setThread(created);
    return created;
  }, [thread, subject]);

  async function send(textArg) {
    const text = (textArg ?? input).trim();
    if (!text || sending) return;
    setInput("");
    setFailed(null);
    const tempId = "tmp-" + Date.now();
    setMessages(m => [...m, { id: tempId, role: "user", content: text }]);
    setSending(true);
    try {
      const t = await ensureThread();
      const reply = await sendChatMessage(t.id, text);
      setMessages(m => [...m, reply]);
      if (reply.thread) {
        setThread(cur => (cur ? {
          ...cur,
          title: reply.thread.title || cur.title,
          subject_code: reply.thread.subject_code ?? cur.subject_code,
          lesson: reply.thread.lesson,
        } : cur));
      }
      refreshThreads();
    } catch (e) {
      setMessages(m => m.filter(x => x.id !== tempId));
      setFailed({
        text,
        error: e.isNetworkError
          ? "Internet yoki server bilan aloqa yo'q. Ulanish tiklangach qayta yuboring."
          : e.message || "AI Ustoz javob bera olmadi.",
      });
      setInput(text);
    } finally {
      setSending(false);
    }
  }

  function onKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  function pickStarter(s) {
    if (s.text.endsWith("\n\n")) {
      setInput(s.text);
      setTimeout(() => {
        const el = inputRef.current;
        el?.focus();
        el?.setSelectionRange(el.value.length, el.value.length);
      }, 0);
    } else {
      send(s.text);
    }
  }

  // textarea balandligini matnga moslash
  useEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 180) + "px";
  }, [input]);

  const activeSubject = thread ? subjectInfo(thread.subject_code) : subjectInfo(subject);
  const groups = useMemo(() => groupThreads(threads), [threads]);
  const isEmpty = !thread && messages.length === 0;

  return (
    <div className="tutor">
      <aside className={"tutor-rail" + (railOpen ? " open" : "")} aria-label="Suhbatlar">
        <button className="tutor-new" onClick={newChat}>
          <PlusIcon /> Yangi suhbat
        </button>
        <div className="tutor-rail-list">
          {threads.length === 0 && <p className="tutor-rail-empty">Suhbatlaringiz shu yerda saqlanadi.</p>}
          {[["today", "Bugun"], ["earlier", "Oldinroq"]].map(([key, label]) =>
            groups[key].length > 0 && (
              <div key={key} className="tutor-rail-group">
                <h3>{label}</h3>
                {groups[key].map(t => (
                  <button
                    key={t.id}
                    className={"tutor-rail-item" + (thread?.id === t.id ? " active" : "")}
                    onClick={() => openThread(t)}
                  >
                    <span className="tutor-rail-title">{t.title || "Yangi suhbat"}</span>
                    {t.subject_name && <span className="tutor-rail-subject">{subjectInfo(t.subject_code)?.label || t.subject_name}</span>}
                    <span className="tutor-rail-delete" role="button" tabIndex={0} aria-label="O'chirish"
                      onClick={e => removeThread(t, e)}
                      onKeyDown={e => e.key === "Enter" && removeThread(t, e)}>
                      <TrashIcon />
                    </span>
                  </button>
                ))}
              </div>
            )
          )}
        </div>
        <button className="tutor-memory-btn" onClick={() => { setMemoryOpen(true); setRailOpen(false); }}>
          <BrainIcon />
          <span>
            <strong>Ustoz xotirasi</strong>
            <small>Ustoz siz haqingizda nimani biladi</small>
          </span>
        </button>
      </aside>
      {railOpen && <div className="tutor-scrim" onClick={() => setRailOpen(false)} />}

      <section className="tutor-main">
        <header className="tutor-head">
          <button className="tutor-icon-btn tutor-rail-toggle" onClick={() => setRailOpen(true)} aria-label="Suhbatlar ro'yxati">
            <MenuIcon />
          </button>
          <div className="tutor-head-title">
            <h1>{thread?.title || "AI Ustoz"}</h1>
            {activeSubject && <span className="tutor-subject-pill">{activeSubject.label}</span>}
          </div>
          {!isOnline && <span className="tutor-offline">Offline</span>}
        </header>
        {status && !status.claude && !status.fallback_ai && (
          <div className="tutor-config-warn" role="alert">
            AI Ustoz serverda sozlanmagan: <code>.env</code> fayliga <code>ANTHROPIC_API_KEY</code> qo'shing va serverni qayta ishga tushiring.
          </div>
        )}
        {thread?.lesson && !thread.lesson.abandoned && <LessonBar lesson={thread.lesson} />}

        <div className="tutor-scroll" ref={listRef}>
          <div className="tutor-column">
            {isEmpty ? (
              <div className="tutor-welcome">
                <TutorMark large />
                <h2>Salom! Bugun nimani o'rganamiz?</h2>
                <p>Fan tanlang va savol bering. Men darajangizni aniqlab, sizga mos mashqlar beraman va yozganingizni tekshiraman.</p>
                <div className="tutor-subjects" role="radiogroup" aria-label="Fan">
                  {available.map(s => (
                    <button key={s.code} role="radio" aria-checked={subject === s.code}
                      className={"tutor-subject" + (subject === s.code ? " on" : "")}
                      onClick={() => setSubject(s.code)}>
                      {s.label}
                    </button>
                  ))}
                </div>
                <div className="tutor-starters">
                  {STARTERS.map(s => (
                    <button key={s.title} className="tutor-starter" onClick={() => pickStarter(s)} disabled={!isOnline}>
                      <strong>{s.title}</strong>
                      <span>{s.text.trim()}</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {loadingThread && <p className="tutor-muted">Yuklanmoqda...</p>}
                {messages.map(m => <Message key={m.id} m={m} />)}
                {sending && (
                  <div className="tmsg assistant">
                    <TutorMark />
                    <div className="tmsg-body"><span className="tutor-typing" aria-label="Ustoz yozmoqda"><i /><i /><i /></span></div>
                  </div>
                )}
              </>
            )}
            {failed && (
              <div className="tutor-error" role="alert">
                <span>{failed.error}</span>
                {failed.text && <button onClick={() => send(failed.text)} disabled={sending}>Qayta yuborish</button>}
              </div>
            )}
          </div>
        </div>

        <div className="tutor-composer-wrap">
          <div className="tutor-composer">
            <textarea
              ref={inputRef}
              rows={1}
              placeholder={isOnline ? "Savolingizni yozing yoki matn tashlang..." : "Internet yo'q: AI Ustoz ulanish tiklangach ishlaydi"}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              disabled={!isOnline}
              maxLength={4000}
            />
            <button className="tutor-icon-btn" onClick={() => setVoiceOpen(true)} disabled={!isOnline}
              aria-label="Ovozli suhbat" title="Ovoz bilan gaplashish">
              <MicIcon />
            </button>
            <button className="tutor-send" onClick={() => send()} disabled={!input.trim() || sending || !isOnline} aria-label="Yuborish">
              <SendIcon />
            </button>
          </div>
          <p className="tutor-hint">Enter — yuborish, Shift+Enter — yangi qator. AI xato qilishi mumkin, muhim narsalarni tekshiring.</p>
        </div>
      </section>

      {memoryOpen && <MemoryPanel onClose={() => setMemoryOpen(false)} />}

      {voiceOpen && (
        <VoiceMode
          subjectCode={activeSubject?.code}
          canChangeSubject={!thread}
          serverStt={!!status?.speech_to_text}
          available={available}
          onPickSubject={setSubject}
          ensureThread={ensureThread}
          onTurn={(msgs, threadInfo) => {
            setMessages(m => [...m, ...msgs.filter(Boolean)]);
            if (threadInfo) setThread(cur => (cur ? { ...cur, ...threadInfo } : cur));
            refreshThreads();
          }}
          onClose={() => setVoiceOpen(false)}
        />
      )}
    </div>
  );
}

const STEP_TYPES = {
  explain: "Tushuntirish", example: "Misollar", exercise: "Mashq",
  quiz: "Mini-test", speaking: "Gapirish", review: "Takrorlash",
};

function LessonBar({ lesson }) {
  const total = lesson.steps.length;
  const done = lesson.steps.filter(s => s.done).length;
  const current = lesson.is_completed ? null : lesson.steps[lesson.current_step];
  return (
    <div className={"lesson-bar" + (lesson.is_completed ? " finished" : "")}>
      <div className="lesson-bar-top">
        <span className="lesson-bar-title">{lesson.title}</span>
        <span className="lesson-bar-count">
          {lesson.is_completed
            ? `Tugadi${lesson.score_percent != null ? ` · ${Math.round(lesson.score_percent)}%` : ""}`
            : `${done}/${total}`}
        </span>
      </div>
      <ol className="lesson-steps" aria-label="Dars qadamlari">
        {lesson.steps.map((s, i) => (
          <li key={i}
            className={[s.done ? "done" : "", s.result ? "r-" + s.result : "", !lesson.is_completed && i === lesson.current_step ? "now" : ""].join(" ")}
            title={`${i + 1}. ${s.title}`}>
            <span className="sr-only">{i + 1}. {s.title}{s.done ? " (bajarildi)" : ""}</span>
          </li>
        ))}
      </ol>
      {current && (
        <p className="lesson-bar-now">
          {lesson.current_step + 1}-qadam: {current.title}
          {STEP_TYPES[current.type] && <span> · {STEP_TYPES[current.type]}</span>}
        </p>
      )}
      {lesson.is_completed && lesson.next_step && <p className="lesson-bar-now">Keyingi dars: {lesson.next_step}</p>}
    </div>
  );
}

const MEMORY_ORDER = ["goal", "interest", "style", "strength", "mistake", "other"];

function MemoryPanel({ onClose }) {
  const [items, setItems] = useState(null);
  const [error, setError] = useState("");
  const [confirmClear, setConfirmClear] = useState(false);

  useEffect(() => {
    fetchTutorMemories()
      .then(list => setItems(list?.results || list || []))
      .catch(() => { setItems([]); setError("Xotirani yuklab bo'lmadi. Internetni tekshiring."); });
    const onKey = e => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  async function remove(id) {
    const prev = items;
    setItems(list => list.filter(x => x.id !== id));
    try { await deleteTutorMemory(id); } catch { setItems(prev); setError("O'chirib bo'lmadi, qayta urinib ko'ring."); }
  }

  async function clearAll() {
    try { await clearTutorMemories(); setItems([]); setConfirmClear(false); }
    catch { setError("O'chirib bo'lmadi, qayta urinib ko'ring."); }
  }

  const groups = MEMORY_ORDER
    .map(cat => ({ cat, list: (items || []).filter(m => m.category === cat) }))
    .filter(g => g.list.length);

  return (
    <div className="mem-scrim" onClick={onClose}>
      <div className="mem-panel" role="dialog" aria-modal="true" aria-labelledby="mem-title" onClick={e => e.stopPropagation()}>
        <header className="mem-head">
          <div>
            <h2 id="mem-title">Ustoz xotirasi</h2>
            <p>Ustoz darslarni sizga moslash uchun shularni eslab qolgan. Keraksizini o'chirib tashlang.</p>
          </div>
          <button className="tutor-icon-btn" onClick={onClose} aria-label="Yopish"><CloseIcon /></button>
        </header>
        <div className="mem-body">
          {items === null && <p className="tutor-muted">Yuklanmoqda...</p>}
          {error && <p className="mem-error" role="alert">{error}</p>}
          {items && items.length === 0 && !error && (
            <p className="mem-empty">
              Hozircha hech narsa yo'q. Ustoz bilan gaplashganingiz sari u qiziqishlaringiz, maqsadingiz va
              ko'p uchraydigan xatolaringizni eslab qoladi.
            </p>
          )}
          {groups.map(g => (
            <section key={g.cat} className="mem-group">
              <h3>{g.list[0].category_label}</h3>
              <ul>
                {g.list.map(m => (
                  <li key={m.id}>
                    <span>{m.text}{m.subject_code && <em> · {subjectInfo(m.subject_code)?.label || m.subject_code}</em>}</span>
                    <button className="mem-del" onClick={() => remove(m.id)} aria-label={`O'chirish: ${m.text}`}><TrashIcon /></button>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
        {items && items.length > 0 && (
          <footer className="mem-foot">
            {confirmClear ? (
              <>
                <span>Hammasi o'chirilsinmi?</span>
                <button className="mem-cancel" onClick={() => setConfirmClear(false)}>Bekor qilish</button>
                <button className="mem-danger" onClick={clearAll}>Ha, o'chirish</button>
              </>
            ) : (
              <button className="mem-cancel" onClick={() => setConfirmClear(true)}>Hammasini o'chirish</button>
            )}
          </footer>
        )}
      </div>
    </div>
  );
}

function Message({ m }) {
  const meta = m.meta || {};
  const tools = [...new Set(meta.tools_used || [])].map(t => TOOL_LABELS[t]).filter(Boolean);
  if (m.role === "user") {
    return (
      <div className="tmsg user">
        <div className="tmsg-body">
          {(meta.mode === "speaking" || meta.mode === "voice") && <span className="tmsg-voice"><MicIcon size={13} /> Ovozli</span>}
          {m.content}
        </div>
      </div>
    );
  }
  return (
    <div className="tmsg assistant">
      <TutorMark />
      <div className="tmsg-body">
        <div className="tmsg-text"><RichText text={m.content} /></div>
        {meta.feedback && <TutorNote text={meta.feedback} />}
        {tools.length > 0 && (
          <div className="tmsg-tools">
            {tools.map(t => <span key={t}><CheckIcon /> {t}</span>)}
          </div>
        )}
      </div>
    </div>
  );
}

function TutorNote({ text, weakWords }) {
  return (
    <aside className="tutor-note">
      <h4>Ustoz izohi</h4>
      <RichText text={text} />
      {weakWords?.length > 0 && (
        <p className="tutor-note-words">
          Yana mashq qiling: {weakWords.map(w => <b key={w}>{w}</b>)}
        </p>
      )}
    </aside>
  );
}

/* ------------------------------------------------------------------ */
/* Ovozli rejim: "Suhbat" (o'zbek/rus/ingliz tilida erkin gaplashish)  */
/* va "Speaking mashqi" (o'rganilayotgan tilda suhbat + tuzatishlar)   */
/* ------------------------------------------------------------------ */

const MAX_RECORD_MS = 60000;
const VOICE_LANG_KEY = "st_voice_lang";
const CHAT_LANGS = [
  { code: "uz-UZ", label: "O'zbekcha" },
  { code: "ru-RU", label: "Русский" },
  { code: "en-US", label: "English" },
];

// Brauzerda o'zbekcha ovoz kam uchraydi: bo'lmasa turkcha (lotin yozuvini yaxshi o'qiydi), keyin istalgani
function pickVoice(lang) {
  const voices = window.speechSynthesis?.getVoices?.() || [];
  const prefix = (lang || "uz").slice(0, 2).toLowerCase();
  return voices.find(v => v.lang?.toLowerCase().startsWith(prefix))
    || (prefix === "uz" ? voices.find(v => v.lang?.toLowerCase().startsWith("tr")) : null)
    || null;
}
const plain = t => String(t || "").replace(/`([^`]*)`/g, "$1").replace(/[*_#>]+/g, "").replace(/^\s*[-•]\s+/gm, "").replace(/\n+/g, " ").trim();

function VoiceMode({ subjectCode, canChangeSubject, available, onPickSubject, ensureThread, onTurn, onClose, serverStt }) {
  const lang = subjectInfo(subjectCode);
  const isLanguage = !!lang?.speech;
  const [mode, setMode] = useState("chat"); // chat | practice
  const [chatLang, setChatLang] = useState(() => { try { return localStorage.getItem(VOICE_LANG_KEY) || "uz-UZ"; } catch { return "uz-UZ"; } });
  const [state, setState] = useState("idle"); // idle | listening | thinking | speaking
  const [last, setLast] = useState(null);
  const [error, setError] = useState("");
  const [browserMode, setBrowserMode] = useState(!serverStt);
  const recorderRef = useRef(null);
  const recognitionRef = useRef(null);
  const audioRef = useRef(null);
  const stopTimer = useRef(null);
  const practice = mode === "practice" && isLanguage;
  const recLang = practice ? lang.speech : chatLang;

  useEffect(() => { setBrowserMode(!serverStt); }, [serverStt]);
  useEffect(() => { window.speechSynthesis?.getVoices?.(); }, []); // ovozlar ro'yxatini oldindan yuklash

  const stopAll = useCallback(() => {
    clearTimeout(stopTimer.current);
    try { if (recorderRef.current?.state === "recording") recorderRef.current.stop(); } catch { /* */ }
    recognitionRef.current?.abort?.();
    audioRef.current?.pause();
    window.speechSynthesis?.cancel();
  }, []);

  useEffect(() => {
    const onKey = e => e.key === "Escape" && close();
    window.addEventListener("keydown", onKey);
    return () => { window.removeEventListener("keydown", onKey); stopAll(); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function close() {
    stopAll();
    recorderRef.current?.stream?.getTracks().forEach(t => t.stop());
    onClose();
  }

  function speakWithBrowser(text, speechLang) {
    if (!window.speechSynthesis) { setState("idle"); return; }
    const u = new SpeechSynthesisUtterance(plain(text).slice(0, 900));
    u.lang = speechLang;
    const voice = pickVoice(speechLang);
    if (voice) u.voice = voice;
    u.onend = u.onerror = () => setState("idle");
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
  }

  function playReply(text, audioBase64, mime, speechLang) {
    setState("speaking");
    if (audioBase64) {
      const audio = new Audio(`data:${mime || "audio/mpeg"};base64,${audioBase64}`);
      audioRef.current = audio;
      audio.onended = () => setState("idle");
      audio.onerror = () => speakWithBrowser(text, speechLang);
      audio.play().catch(() => speakWithBrowser(text, speechLang));
    } else {
      speakWithBrowser(text, speechLang);
    }
  }

  async function startRecording() {
    setError("");
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setBrowserMode(true);
      return startBrowserRecognition();
    }
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setError("Mikrofonga ruxsat berilmadi. Brauzer manzil satridagi qulf belgisidan mikrofonni yoqing.");
      return;
    }
    const type = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg"].find(t => MediaRecorder.isTypeSupported?.(t));
    const rec = new MediaRecorder(stream, type ? { mimeType: type } : undefined);
    const chunks = [];
    rec.ondataavailable = e => e.data.size && chunks.push(e.data);
    rec.onstop = async () => {
      stream.getTracks().forEach(t => t.stop());
      clearTimeout(stopTimer.current);
      const blob = new Blob(chunks, { type: rec.mimeType || "audio/webm" });
      if (blob.size < 1500) { setState("idle"); setError("Juda qisqa. Tugmani bosing, gapiring, tugatgach yana bosing."); return; }
      await uploadTurn(blob, rec.mimeType);
    };
    recorderRef.current = rec;
    rec.start();
    setState("listening");
    stopTimer.current = setTimeout(() => rec.state === "recording" && rec.stop(), MAX_RECORD_MS);
  }

  async function uploadTurn(blob, mime) {
    setState("thinking");
    const ext = (mime || "").includes("mp4") ? "m4a" : (mime || "").includes("ogg") ? "ogg" : "webm";
    try {
      const t = await ensureThread(practice ? subjectCode : subjectCode);
      const res = practice
        ? await sendSpeakingAudio(t.id, blob, `speech.${ext}`)
        : await sendVoiceAudio(t.id, blob, `voice.${ext}`);
      onTurn([res.user_message, res.reply], res.thread);
      setLast({ heard: res.user_message?.content, reply: res.reply.content, feedback: res.reply.meta?.feedback, weak: res.weak_words });
      playReply(res.reply.content, res.audio_base64, res.audio_mime, res.speech_lang || (practice ? lang.speech : chatLang));
    } catch (e) {
      setState("idle");
      if (e.status === 501 || e.status === 500) {
        setBrowserMode(true);
        setError(SpeechRecognitionApi
          ? "Serverda ovozni tanish ishlamadi, brauzerning o'zi orqali tanishga o'tdim. Yana bir bor gapiring."
          : "Serverda ovozni tanish ishlamadi va bu brauzer ham ovozni taniy olmaydi. Chrome yoki Edge'da oching yoki matn bilan yozing.");
      } else {
        setError(e.isNetworkError ? "Internet bilan aloqa yo'q." : e.message || "Javob olib bo'lmadi.");
      }
    }
  }

  function startBrowserRecognition() {
    if (!SpeechRecognitionApi) {
      setError("Bu brauzer ovozni taniy olmaydi. Chrome yoki Edge'da oching yoki matn bilan yozing.");
      return;
    }
    setError("");
    const rec = new SpeechRecognitionApi();
    rec.lang = recLang;
    rec.interimResults = false;
    rec.onstart = () => setState("listening");
    rec.onerror = ev => {
      setState("idle");
      if (ev.error === "not-allowed") setError("Mikrofonga ruxsat berilmadi.");
      else if (ev.error === "no-speech") setError("Ovoz eshitilmadi. Yana urinib ko'ring.");
      else if (ev.error === "language-not-supported") setError("Brauzer bu tilni tanimaydi. Boshqa tilni tanlang.");
      else if (ev.error !== "aborted") setError("Ovozni tanib bo'lmadi. Yana urinib ko'ring.");
    };
    rec.onend = () => setState(s => (s === "listening" ? "idle" : s));
    rec.onresult = async e => {
      const heard = e.results[0][0].transcript;
      setState("thinking");
      try {
        const t = await ensureThread(subjectCode);
        const reply = await sendChatMessage(t.id, heard);
        onTurn([{ id: "v-" + Date.now(), role: "user", content: heard, meta: { mode: "voice" } }, reply], reply.thread);
        setLast({ heard, reply: reply.content });
        playReply(reply.content, null, null, recLang);
      } catch (err) {
        setState("idle");
        setError(err.message || "Javob olib bo'lmadi.");
      }
    };
    recognitionRef.current = rec;
    rec.start();
  }

  function onMic() {
    if (state === "listening") {
      if (recorderRef.current?.state === "recording") recorderRef.current.stop();
      recognitionRef.current?.stop();
      return;
    }
    if (state === "speaking") { stopAll(); setState("idle"); return; }
    if (state === "thinking") return;
    window.speechSynthesis?.cancel();
    browserMode ? startBrowserRecognition() : startRecording();
  }

  const label = {
    idle: last ? "Javob berish uchun mikrofonni bosing" : practice ? "Mikrofonni bosing va o'rganayotgan tilingizda gapiring" : "Mikrofonni bosing va savolingizni ayting",
    listening: "Tinglayapman... tugatgach yana bosing",
    thinking: "O'ylayapman...",
    speaking: "Ustoz gapirmoqda. To'xtatish uchun bosing",
  }[state];

  const needsPick = mode === "practice" && !isLanguage;

  return (
    <div className="voice" role="dialog" aria-modal="true" aria-label="Ovozli suhbat">
      <button className="voice-close" onClick={close} aria-label="Yopish"><CloseIcon /></button>

      <div className="voice-modes" role="tablist">
        <button role="tab" aria-selected={mode === "chat"} className={mode === "chat" ? "on" : ""} onClick={() => { stopAll(); setState("idle"); setMode("chat"); setLast(null); }}>Ustoz bilan suhbat</button>
        <button role="tab" aria-selected={mode === "practice"} className={mode === "practice" ? "on" : ""} onClick={() => { stopAll(); setState("idle"); setMode("practice"); setLast(null); }}>Speaking mashqi</button>
      </div>

      {needsPick ? (
        <div className="voice-pick">
          <h2>Qaysi tilda mashq qilamiz?</h2>
          <p>Speaking mashqi til fanlari uchun. Ustoz o'rganayotgan tilingizda suhbatlashadi va xatolarni ko'rsatadi.</p>
          {canChangeSubject ? (
            <div className="tutor-subjects">
              {available.filter(s => s.speech).map(s => (
                <button key={s.code} className="tutor-subject dark" onClick={() => onPickSubject(s.code)}>{s.label}</button>
              ))}
            </div>
          ) : (
            <p>Bu suhbat til fani bo'yicha emas. Speaking uchun yangi suhbat ochib, til tanlang.</p>
          )}
        </div>
      ) : (
        <>
          <div className="voice-lang">
            {practice ? lang.label : (
              <select value={chatLang} onChange={e => { setChatLang(e.target.value); try { localStorage.setItem(VOICE_LANG_KEY, e.target.value); } catch { /* */ } }}
                aria-label="Gapiradigan tilingiz" disabled={!browserMode}>
                {CHAT_LANGS.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
              </select>
            )}
            {!practice && !browserMode && <span className="voice-auto">til avtomatik aniqlanadi</span>}
          </div>
          <button className={"voice-orb " + state} onClick={onMic} aria-label={label}>
            <span className="voice-orb-core"><MicIcon size={34} /></span>
          </button>
          <p className="voice-label" aria-live="polite">{label}</p>
          {error && <p className="voice-error" role="alert">{error}</p>}

          {last && (
            <div className="voice-captions">
              {last.heard && <p className="voice-heard"><span>Siz:</span> {last.heard}</p>}
              <div className="voice-reply">{practice ? last.reply : <RichText text={last.reply} />}</div>
              {(last.feedback || last.weak?.length > 0) && <TutorNote text={last.feedback || ""} weakWords={last.weak} />}
            </div>
          )}
        </>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */

function TutorMark({ large }) {
  return (
    <span className={"tutor-mark" + (large ? " large" : "")} aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none">
        <path d="M3 9.5 12 5l9 4.5-9 4.5-9-4.5Z" fill="currentColor" />
        <path d="M7 11.8V16c0 1.4 2.2 2.8 5 2.8s5-1.4 5-2.8v-4.2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
    </span>
  );
}
const svgProps = size => ({ width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.9, strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": true });
function MicIcon({ size = 19 }) { return <svg {...svgProps(size)}><rect x="9" y="3" width="6" height="12" rx="3" /><path d="M19 11a7 7 0 0 1-14 0M12 18v3" /></svg>; }
function SendIcon() { return <svg {...svgProps(18)}><path d="M12 19V5M5 12l7-7 7 7" /></svg>; }
function PlusIcon() { return <svg {...svgProps(16)}><path d="M12 5v14M5 12h14" /></svg>; }
function MenuIcon() { return <svg {...svgProps(20)}><path d="M4 7h16M4 12h16M4 17h10" /></svg>; }
function TrashIcon() { return <svg {...svgProps(15)}><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3" /></svg>; }
function CloseIcon() { return <svg {...svgProps(18)}><path d="M6 6l12 12M18 6 6 18" /></svg>; }
function BrainIcon() { return <svg {...svgProps(18)}><path d="M9 4a3 3 0 0 0-3 3 3 3 0 0 0-2 5 3 3 0 0 0 2 5 3 3 0 0 0 3 3h0a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2Z" /><path d="M15 4a3 3 0 0 1 3 3 3 3 0 0 1 2 5 3 3 0 0 1-2 5 3 3 0 0 1-3 3h0a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z" /></svg>; }
function CheckIcon() { return <svg {...svgProps(12)}><path d="m5 12 5 5L20 7" /></svg>; }
