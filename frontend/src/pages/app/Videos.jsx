import React, { useEffect, useState } from "react";
import {
  fetchRecommendedVideos,
  fetchSavedVideos,
  saveVideo,
  markVideoClicked,
} from "../../api/client.js";
import "./Videos.css";

const listify = (data) =>
  Array.isArray(data) ? data : data?.results || [];

function getYoutubeId(value) {
  if (!value) return "";

  // Agar backend faqat ID yuborsa
  if (!value.includes("http")) {
    return value;
  }

  // https://www.youtube.com/watch?v=XXXXXXXX
  try {
    const url = new URL(value);

    if (url.hostname.includes("youtube.com")) {
      return url.searchParams.get("v") || "";
    }

    // https://youtu.be/XXXXXXXX
    if (url.hostname === "youtu.be") {
      return url.pathname.replace("/", "");
    }
  } catch {
    return value;
  }

  return value;
}

function toVideoItem(r) {
  const v = r.video || r;

  return {
    id: v.id,
    recId: r.video ? r.id : null,

    // Backenddan kelayotgan youtube_id
    youtubeId: getYoutubeId(v.youtube_id),

    title: v.title,
    channel: v.channel_title,

    duration: v.duration_seconds
      ? `${Math.ceil(v.duration_seconds / 60)} daq`
      : "—",

    difficulty: v.difficulty,
    rating: v.avg_rating,
    thumbnail: v.thumbnail_url,
  };
}

export default function Videos() {
  const [tab, setTab] = useState("recommended");
  const [recommended, setRecommended] = useState([]);
  const [saved, setSaved] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [playing, setPlaying] = useState(null);

async function load() {
  setLoading(true);
  setError("");

  try {
    const [recData, savedData] = await Promise.all([
      fetchRecommendedVideos(),
      fetchSavedVideos(),
    ]);

    console.log("REC:", recData);
    console.log("SAVED:", savedData);

    setRecommended(listify(recData).map(toVideoItem));
    setSaved(listify(savedData).map(toVideoItem));
  } catch (e) {
    console.error("VIDEO ERROR:", e);
    setError(e.message || "Videolarni yuklab bo'lmadi.");
  } finally {
    setLoading(false);
  }
}

  useEffect(() => {
    load();
  }, []);

  async function handleSave(video) {
    if (saved.some((v) => v.id === video.id)) return;

    try {
      await saveVideo(video.id);
      setSaved((s) => [...s, video]);
    } catch (e) {
      setError(e.message || "Videoni saqlab bo'lmadi.");
    }
  }

  function handleOpen(video) {
    if (video.recId) {
      markVideoClicked(video.recId).catch(() => {});
    }

    if (video.youtubeId) {
      setPlaying(video);
    }
  }

  const list = tab === "recommended" ? recommended : saved;

  return (
    <div>
      <h1 className="page-title">Video tavsiyalar</h1>

      <p className="page-sub">
        Dars va mashqlar natijalariga mos backend tavsiyalari
      </p>

      <div className="tab-row">
        <button
          className={"tab-btn" + (tab === "recommended" ? " active" : "")}
          onClick={() => setTab("recommended")}
        >
          Tavsiya etilgan
        </button>

        <button
          className={"tab-btn" + (tab === "saved" ? " active" : "")}
          onClick={() => setTab("saved")}
        >
          Saqlanganlar
        </button>
      </div>

      {loading && (
        <div className="page-sub" style={{ marginTop: 20 }}>
          Yuklanmoqda...
        </div>
      )}

      {error && (
        <div
          className="math-feedback wrong"
          style={{ marginTop: 16 }}
        >
          {error}
        </div>
      )}

      {!loading && !list.length && !error && (
        <div className="page-sub" style={{ marginTop: 20 }}>
          {tab === "recommended"
            ? "Siz uchun hozircha video tavsiyasi yo'q."
            : "Saqlangan video yo'q."}
        </div>
      )}

      <div className="video-grid">
        {list.map((v) => (
          <div key={v.id} className="video-card">
            <div
              className="video-thumb"
              onClick={() => handleOpen(v)}
              style={{
                cursor: v.youtubeId ? "pointer" : "default",
                backgroundImage: v.thumbnail
                  ? `url(${v.thumbnail})`
                  : undefined,
              }}
            >
              {!v.thumbnail && "▶"}
            </div>

            <div className="video-body">
              <div className="video-title">
                {v.title}
              </div>

              <div className="video-meta">
                <span>{v.channel || "YouTube"}</span>
                <span>{v.duration}</span>
              </div>

              <div className="video-actions">
                {v.difficulty && (
                  <span className="video-tag">
                    {v.difficulty}
                  </span>
                )}

                {v.rating != null && (
                  <span className="video-tag">
                    ⭐ {v.rating}
                  </span>
                )}

                {tab === "recommended" && (
                  <button
                    className="btn btn-outline"
                    style={{
                      padding: "5px 12px",
                      fontSize: 12,
                    }}
                    onClick={() => handleSave(v)}
                    disabled={saved.some(
                      (s) => s.id === v.id
                    )}
                  >
                    {saved.some((s) => s.id === v.id)
                      ? "Saqlangan"
                      : "Saqlash"}
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* VIDEO OYNATISH MODALI */}
      {playing && (
        <div
          className="modal-backdrop"
          onClick={() => setPlaying(null)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              width: "min(880px, 92vw)",
              aspectRatio: "16/9",
              background: "#000",
              borderRadius: 12,
              overflow: "hidden",
            }}
          >
            <iframe
              width="100%"
              height="100%"
              src={`https://www.youtube.com/embed/${playing.youtubeId}?autoplay=1`}
              title={playing.title || "YouTube video"}
              allow="autoplay; encrypted-media; picture-in-picture"
              allowFullScreen
            />
          </div>
        </div>
      )}
    </div>
  );
}
