import React, { useEffect, useMemo, useState } from "react";
import { overallCards as mockOverall, subjectStats as mockSubjects, heatmapCells as mockHeatmapCells } from "../../data/mockData.js";
import { fetchDashboard } from "../../api/client.js";
import "./Dashboard.css";

const PERIODS = [
  { key: "daily", label: "Kunlik" },
  { key: "weekly", label: "Haftalik" },
  { key: "monthly", label: "Oylik" },
  { key: "yearly", label: "Yillik" },
];

function BarChart({ points }) {
  const max = Math.max(1, ...points.map(p => p.minutes));
  return (
    <div className="bar-chart">
      {points.map((p, i) => (
        <div className="bar-chart-col" key={i} title={`${p.label}: ${p.minutes} daq, ${p.sessions} sessiya`}>
          <div className="bar-chart-bar-track">
            <div className="bar-chart-bar" style={{ height: `${Math.max(3, (p.minutes / max) * 100)}%` }} />
          </div>
          <div className="bar-chart-label">{p.label}</div>
        </div>
      ))}
    </div>
  );
}

export default function Dashboard() {
  const [overallCards, setOverallCards] = useState(mockOverall);
  const [subjectStats, setSubjectStats] = useState(mockSubjects);
  const [usingDemoData, setUsingDemoData] = useState(false);
  const [heatmap, setHeatmap] = useState(null);
  const [series, setSeries] = useState(null);
  const [growth, setGrowth] = useState(18);
  const [period, setPeriod] = useState("daily");

  useEffect(() => {
    fetchDashboard()
      .then(data => {
        setOverallCards([
          { label: "Umumiy soat", value: (data.total_minutes / 60).toFixed(1) },
          { label: "Sessiyalar", value: String(data.total_sessions) },
          { label: "Umumiy ball", value: String(data.subjects.reduce((a, s) => a + (s.total_points || 0), 0)) },
          { label: "Streak", value: "🔥 " + Math.max(0, ...data.subjects.map(s => s.current_streak_days || 0)) + " kun" },
        ]);
        setSubjectStats(data.subjects.map(s => ({
          name: s.subject_code, level: "—", minutes: s.total_minutes, sessions: s.sessions_completed,
          pronunciation: Math.round(s.avg_pronunciation_score || 0), streak: s.current_streak_days,
        })));
        setSeries(data.series || null);
        setGrowth(data.growth_percent ?? 0);

        // Haqiqiy heatmap: oxirgi 90 kunlik faollikni kun bo'yicha jamlaymiz
        const byDate = {};
        (data.heatmap || []).forEach(h => {
          byDate[h.date] = (byDate[h.date] || 0) + (h.minutes_spent || 0);
        });
        const days = Object.keys(byDate).sort();
        const cells = days.slice(-98).map(d => {
          const mins = byDate[d];
          const color = mins <= 0 ? "var(--border)" : mins < 15 ? "oklch(0.55 0.15 155 / 0.35)" : mins < 40 ? "oklch(0.55 0.15 155 / 0.7)" : "oklch(0.55 0.15 155)";
          return { color, date: d, minutes: mins };
        });
        setHeatmap(cells.length ? cells : null);
      })
      .catch(() => setUsingDemoData(true));
  }, []);

  const activePoints = series ? series[period] : null;

  return (
    <div>
      <h1 className="page-title">Xush kelibsiz, Aziz</h1>
      <p className="page-sub">Bugungi progress va statistikangiz{usingDemoData && " (demo ma'lumot — backend ulanmagan)"}</p>

      <div className="stat-grid">
        {overallCards.map((c, i) => (
          <div key={i} className="stat-card">
            <div className="stat-label">{c.label}</div>
            <div className="stat-value">{c.value}</div>
          </div>
        ))}
      </div>

      <div className="subject-grid">
        {subjectStats.map((s, i) => (
          <div key={i} className="subject-card">
            <div className="subject-head">
              <div className="subject-name">{s.name}</div>
              <div className="subject-level">{s.level}</div>
            </div>
            <div className="metric-grid">
              <div><div className="metric-label">O'qilgan vaqt</div><div className="metric-value">{s.minutes} daq</div></div>
              <div><div className="metric-label">Sessiyalar</div><div className="metric-value">{s.sessions}</div></div>
              <div><div className="metric-label">Talaffuz</div><div className="metric-value">{s.pronunciation}%</div></div>
              <div><div className="metric-label">Streak</div><div className="metric-value">🔥 {s.streak} kun</div></div>
            </div>
          </div>
        ))}
      </div>

      <div className="panel" style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14, flexWrap: "wrap", gap: 10 }}>
          <div style={{ fontWeight: 700, fontSize: 15 }}>Faollik statistikasi</div>
          <div className="period-tabs">
            {PERIODS.map(p => (
              <button
                key={p.key}
                className={"period-tab" + (period === p.key ? " active" : "")}
                onClick={() => setPeriod(p.key)}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
        {activePoints ? (
          <BarChart points={activePoints} />
        ) : (
          <div className="page-sub">Statistika hali yig'ilmagan — birinchi darsni yakunlaganingizdan so'ng bu yerda grafik chiqadi.</div>
        )}
      </div>

      <div className="bottom-grid">
        <div className="panel">
          <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 14 }}>Faollik (oxirgi ~14 hafta)</div>
          <div className="heatmap-grid">
            {(heatmap || mockHeatmapCells).map((c, i) => <div key={i} className="heatmap-cell" title={c.date ? `${c.date}: ${c.minutes} daq` : undefined} style={{ background: c.color }} />)}
          </div>
        </div>
        <div className="panel">
          <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 10 }}>Haftalik hisobot</div>
          <div className="growth" style={{ color: growth >= 0 ? "oklch(0.55 0.15 155)" : "oklch(0.6 0.18 25)" }}>
            {growth >= 0 ? "+" : ""}{growth}%
          </div>
          <div style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 16 }}>o'tgan haftaga nisbatan</div>
          <button className="btn btn-outline" style={{ width: "100%" }}>PDF yuklab olish</button>
        </div>
      </div>
    </div>
  );
}
