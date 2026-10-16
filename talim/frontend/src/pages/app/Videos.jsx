import React, { useEffect, useRef, useState } from "react";
import {
  addWatchHistory, fetchRecommendedVideos, fetchSavedVideos, markVideoClicked, removeSavedVideo, saveVideo, searchYoutube,
} from "../../api/client.js";
import "./ui.css";
import "./Videos.css";

const listify = d => (Array.isArray(d) ? d : d?.results || []);
const DURATIONS = [
  { key: "", label: "Har qanday" },
  { key: "short", label: "4 daq gacha" },
  { key: "medium", label: "4–20 daq" },
  { key: "long", label: "20+ daq" },
];
const TABS = [
  { key: "search", label: "Qidiruv" },
  { key: "recommended", label: "Tavsiyalar" },
  { key: "saved", label: "Saqlanganlar" },
];

function fmtDuration(s) {
  if (!s) return null;
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
  return h ? `${h}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}` : `${m}:${String(sec).padStart(2, "0")}`;
}
function fmtViews(n) {
  if (!n) return null;
  if (n >= 1e6) return `${(n / 1e6).toFixed(1).replace(".0", "")} mln ko'rish`;
  if (n >= 1e3) return `${Math.round(n / 1e3)} ming ko'rish`;
  return `${n} ko'rish`;
}
const toItem = r => {
  const v = r.video || r;
  return { ...v, recId: r.video ? r.id : null, savedId: r.video && r.created_at && !r.reason ? r.id : null };
};

export default function Videos() {
  const [tab, setTab] = useState("search");
  const [q, setQ] = useState("");
  const [duration, setDuration] = useState("");
  const [results, setResults] = useState(null);
  const [lastQuery, setLastQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [notice, setNotice] = useState("");
  const [searching, setSearching] = useState(false);
  const [recommended, setRecommended] = useState(null);
  const [saved, setSaved] = useState([]);
  const [error, setError] = useState("");
  const [playing, setPlaying] = useState(null);
  const inputRef = useRef(null);

  useEffect(() => {
    searchYoutube("").then(d => setSuggestions(d.queries || [])).catch(() => {});
    fetchSavedVideos().then(d => setSaved(listify(d).map(s => ({ ...s.video, savedId: s.id })))).catch(() => {});
  }, []);

  useEffect(() => {
    if (tab === "recommended" && recommended === null) {
      fetchRecommendedVideos().then(d => setRecommended(listify(d).map(toItem))).catch(() => setRecommended([]));
    }
  }, [tab, recommended]);

  async function runSearch(query, dur = duration) {
    const text = (query ?? q).trim();
    if (!text) { inputRef.current?.focus(); return; }
    setQ(text); setTab("search"); setSearching(true); setError(""); setNotice("");
    try {
      const d = await searchYoutube(text, dur);
      setResults(d.results || []);
      setLastQuery(text);
      setNotice(d.source === "local" ? d.notice : "");
    } catch (e) {
      setError(e.status === 429 ? "Juda ko'p qidiruv. Bir daqiqadan keyin urinib ko'ring." : e.message || "Qidirib bo'lmadi.");
    } finally {
      setSearching(false);
    }
  }

  const isSaved = v => saved.some(s => s.id === v.id || s.youtube_id === v.youtube_id);

  async function toggleSave(v) {
    const existing = saved.find(s => s.id === v.id || s.youtube_id === v.youtube_id);
    try {
      if (existing) {
        await removeSavedVideo(existing.savedId);
        setSaved(list => list.filter(s => s !== existing));
      } else {
        const res = await saveVideo(v.id);
        setSaved(list => [{ ...v, savedId: res.id }, ...list]);
      }
    } catch (e) {
      setError(e.message || "Saqlab bo'lmadi.");
    }
  }

  function open(v) {
    setPlaying(v);
    if (v.recId) markVideoClicked(v.recId).catch(() => {});
    addWatchHistory(v.id).catch(() => {});
  }

  const list = tab === "search" ? results : tab === "recommended" ? recommended : saved;

  return (
    <div className="ui vids">
      <header className="ui-head">
        <div>
          <h1>Video darslar</h1>
          <p>YouTube'dan istalgan mavzuni toping va shu yerning o'zida ko'ring. Yoqqanini saqlab qo'ying.</p>
        </div>
      </header>

      <form className="vids-search" onSubmit={e => { e.preventDefault(); runSearch(); }} role="search">
        <svg className="vids-search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>
        <input ref={inputRef} value={q} onChange={e => setQ(e.target.value)} placeholder="Masalan: Present Perfect, IELTS speaking, kvadrat tenglama..." aria-label="Video qidirish" />
        <button className="ui-btn primary" disabled={searching}>{searching ? "Qidirilmoqda..." : "Qidirish"}</button>
      </form>

      <div className="vids-filters">
        <div className="ui-chips" aria-label="Tavsiya etilgan qidiruvlar">
          {suggestions.map(s => <button key={s} className="ui-chip" onClick={() => runSearch(s)}>{s}</button>)}
        </div>
        <div className="ui-tabs" aria-label="Davomiyligi">
          {DURATIONS.map(d => (
            <button key={d.key} className={duration === d.key ? "on" : ""}
              onClick={() => { setDuration(d.key); if (lastQuery) runSearch(lastQuery, d.key); }}>{d.label}</button>
          ))}
        </div>
      </div>

      <div className="ui-tabs vids-tabs" role="tablist">
        {TABS.map(t => (
          <button key={t.key} role="tab" aria-selected={tab === t.key} className={tab === t.key ? "on" : ""} onClick={() => setTab(t.key)}>
            {t.label}{t.key === "saved" && saved.length > 0 && ` (${saved.length})`}
          </button>
        ))}
      </div>

      {notice && tab === "search" && <div className="ui-alert">{notice}</div>}
      {error && <div className="ui-alert bad">{error}</div>}

      {tab === "search" && results === null && !searching && (
        <div className="ui-card ui-empty"><strong>Nimani o'rganmoqchisiz?</strong>Mavzuni yozing yoki yuqoridagi tavsiyalardan birini tanlang.</div>
      )}
      {(searching || (tab === "recommended" && recommended === null)) && (
        <div className="vids-grid">{[0, 1, 2, 3, 4, 5].map(i => <div key={i} className="ui-skeleton" style={{ aspectRatio: "16 / 13" }} />)}</div>
      )}
      {!searching && list && list.length === 0 && (
        <div className="ui-card ui-empty">
          {tab === "search" ? <><strong>Hech narsa topilmadi</strong>Boshqa so'z bilan qidirib ko'ring.</> :
            tab === "saved" ? <><strong>Saqlangan video yo'q</strong>Video ostidagi "Saqlash" tugmasini bosing.</> :
              <><strong>Hozircha tavsiya yo'q</strong>Dars va mashqlardan keyin tavsiyalar paydo bo'ladi.</>}
        </div>
      )}
      {!searching && list && list.length > 0 && (
        <div className="vids-grid">
          {list.map(v => (
            <article key={v.id || v.youtube_id} className="vid">
              <button className="vid-thumb" onClick={() => open(v)} aria-label={`Ko'rish: ${v.title}`}>
                {v.thumbnail_url ? <img src={v.thumbnail_url} alt="" loading="lazy" /> : <span className="vid-thumb-empty" />}
                {fmtDuration(v.duration_seconds) && <span className="vid-dur">{fmtDuration(v.duration_seconds)}</span>}
                <span className="vid-play" aria-hidden="true"><svg width="22" height="22" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" fill="currentColor" /></svg></span>
              </button>
              <div className="vid-body">
                <h3 className="vid-title" onClick={() => open(v)}>{v.title}</h3>
                <p className="vid-meta">{v.channel_title || "YouTube"}{fmtViews(v.view_count) && ` · ${fmtViews(v.view_count)}`}</p>
                <button className={"vid-save" + (isSaved(v) ? " on" : "")} onClick={() => toggleSave(v)} aria-pressed={isSaved(v)}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill={isSaved(v) ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M6 3h12v18l-6-4-6 4z" /></svg>
                  {isSaved(v) ? "Saqlangan" : "Saqlash"}
                </button>
              </div>
            </article>
          ))}
        </div>
      )}

      {playing && <Player v={playing} saved={isSaved(playing)} onSave={() => toggleSave(playing)} onClose={() => setPlaying(null)} />}
    </div>
  );
}

function Player({ v, saved, onSave, onClose }) {
  useEffect(() => {
    const onKey = e => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => { window.removeEventListener("keydown", onKey); document.body.style.overflow = ""; };
  }, [onClose]);
  return (
    <div className="vid-modal" onClick={onClose} role="dialog" aria-modal="true" aria-label={v.title}>
      <div className="vid-modal-box" onClick={e => e.stopPropagation()}>
        <div className="vid-frame">
          <iframe src={`https://www.youtube-nocookie.com/embed/${v.youtube_id}?autoplay=1&rel=0`} title={v.title}
            allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowFullScreen />
        </div>
        <div className="vid-modal-info">
          <div>
            <h2>{v.title}</h2>
            <p>{v.channel_title}</p>
          </div>
          <div className="vid-modal-actions">
            <button className="ui-btn sm" onClick={onSave}>{saved ? "Saqlangan" : "Saqlash"}</button>
            <a className="ui-btn sm" href={`https://www.youtube.com/watch?v=${v.youtube_id}`} target="_blank" rel="noreferrer">YouTube'da ochish</a>
            <button className="ui-btn sm ink" onClick={onClose}>Yopish</button>
          </div>
        </div>
      </div>
    </div>
  );
}
