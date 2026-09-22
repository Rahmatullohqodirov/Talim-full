import React, { useEffect, useState, useRef } from "react";
import { externalCourses as mockCourses } from "../../data/mockData.js";
import {
  fetchExternalCourses,
  fetchSavedExternalCourses,
  saveExternalCourse,
} from "../../api/client.js";
import "./Videos.css";

const SOURCES = [
  { id: "all", label: "Barchasi" },
  { id: "linkedin_learning", label: "LinkedIn Learning" },
  { id: "coursera", label: "Coursera" },
  { id: "khan_academy", label: "Khan Academy" },
  { id: "google_books", label: "Google Books" },
];

function normalize(data) {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  if (Array.isArray(data.results)) return data.results;
  return [];
}

export default function Courses() {
  const [source, setSource] = useState("all");
  const [courses, setCourses] = useState([]);
  const [savedIds, setSavedIds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [usingMock, setUsingMock] = useState(false);

  // Kurslarni yuklash — source o'zgarganda bir marta chaqiriladi
  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    fetchExternalCourses(source === "all" ? null : source)
      .then((data) => {
        if (cancelled) return;
        const list = normalize(data);
        if (list.length > 0) {
          setCourses(list);
          setUsingMock(false);
        } else {
          setCourses(mockCourses.filter((c) => source === "all" || c.source === source));
          setUsingMock(true);
        }
      })
      .catch(() => {
        if (cancelled) return;
        setCourses(mockCourses.filter((c) => source === "all" || c.source === source));
        setUsingMock(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [source]);

  // Saqlangan kurslarni bir marta yuklash
  useEffect(() => {
    let cancelled = false;

    fetchSavedExternalCourses()
      .then((data) => {
        if (cancelled) return;
        const list = normalize(data);
        setSavedIds(list.map((s) => s.course?.id ?? s.id).filter(Boolean));
      })
      .catch(() => {});

    return () => { cancelled = true; };
  }, []);

  function handleSave(course) {
    if (savedIds.includes(course.id)) return;
    setSavedIds((ids) => [...ids, course.id]);
    if (!usingMock) {
      saveExternalCourse(course.id).catch(() => {
        setSavedIds((ids) => ids.filter((id) => id !== course.id));
      });
    }
  }

  return (
    <div>
      <h1 className="page-title">Tashqi kurslar</h1>
      <p className="page-sub">
        LinkedIn Learning, Coursera, Khan Academy va Google Books orqali
        qo'shimcha materiallar
      </p>

      <div className="tab-row">
        {SOURCES.map((s) => (
          <button
            key={s.id}
            className={"tab-btn" + (source === s.id ? " active" : "")}
            onClick={() => setSource(s.id)}
          >
            {s.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ color: "var(--text-muted)", fontSize: 14, marginTop: 24 }}>
          Yuklanmoqda...
        </div>
      ) : (
        <div className="video-grid">
          {courses.map((c) => (
            <div key={c.id} className="video-card">
              <div className="video-thumb">▶</div>
              <div className="video-body">
                <div className="video-title">{c.title}</div>
                <div className="video-meta">
                  <span>{c.source_label}</span>
                  <span>{c.level}</span>
                </div>
                <div className="video-actions">
                  {c.is_premium_only && (
                    <span className="video-tag">Premium</span>
                  )}
                  <a
                    className="btn btn-outline"
                    style={{ padding: "5px 12px", fontSize: 12 }}
                    href={c.url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Ko'rish
                  </a>
                  <button
                    className="btn btn-outline"
                    style={{ padding: "5px 12px", fontSize: 12 }}
                    onClick={() => handleSave(c)}
                    disabled={savedIds.includes(c.id)}
                  >
                    {savedIds.includes(c.id) ? "Saqlangan" : "Saqlash"}
                  </button>
                </div>
              </div>
            </div>
          ))}

          {courses.length === 0 && (
            <div style={{ color: "var(--text-muted)", fontSize: 14 }}>
              Bu bo'limda hozircha kurs yo'q.
            </div>
          )}
        </div>
      )}

      {usingMock && (
        <div style={{ color: "var(--text-muted)", fontSize: 12.5, marginTop: 12 }}>
          (Demo) Backenddan ma'lumot kelmadi — namuna kurslar ko'rsatilmoqda.
        </div>
      )}
    </div>
  );
}