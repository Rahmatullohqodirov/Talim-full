import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { fetchDashboard, toggleStudyPlanItem } from "../../api/client.js";
import "./ui.css";
import "./Dashboard.css";

const SUBJECT_LABELS = {
  english: "Ingliz tili", german: "Nemis tili", russian: "Rus tili",
  turkish: "Turk tili", uzbek: "O'zbek tili", math: "Matematika",
};
const PERIOD_TABS = [
  { key: "daily", label: "Kunlik" },
  { key: "weekly", label: "Haftalik" },
  { key: "monthly", label: "Oylik" },
];
const PLAN_PROMPTS = {
  daily: "Menga bugun uchun kunlik o'quv reja tuzib bering.",
  weekly: "Menga shu hafta uchun haftalik o'quv reja tuzib bering.",
  monthly: "Menga bir oylik o'quv reja tuzib bering.",
};
const TYPE_LABELS = {
  lesson: "Dars", vocabulary: "So'zlar", quiz: "Quiz", flashcard: "Flashcard", speaking: "Speaking",
  video: "Video", grammar: "Grammatika", reading: "O'qish", writing: "Yozish", math: "Matematika",
};
const CHART_PERIODS = [
  { key: "daily", label: "30 kun" },
  { key: "weekly", label: "12 hafta" },
  { key: "monthly", label: "12 oy" },
];

function greeting() {
  const h = new Date().getHours();
  if (h < 5) return "Xayrli tun";
  if (h < 12) return "Xayrli tong";
  if (h < 18) return "Xayrli kun";
  return "Xayrli kech";
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [planTab, setPlanTab] = useState(null);
  const [chartPeriod, setChartPeriod] = useState("daily");
  const navigate = useNavigate();

  useEffect(() => {
    fetchDashboard()
      .then(d => {
        setData(d);
        const first = PERIOD_TABS.find(t => (d.plans || []).some(p => p.period === t.key));
        setPlanTab(first ? first.key : "weekly");
      })
      .catch(e => setError(e.isNetworkError ? "Server bilan aloqa yo'q. Internetni tekshirib, sahifani yangilang." : e.message));
  }, []);

  if (error) {
    return <div className="ui"><div className="ui-alert bad">{error}</div></div>;
  }
  if (!data) {
    return (
      <div className="ui dash" aria-busy="true">
        <div className="ui-skeleton" style={{ height: 40, width: 280, marginBottom: 24 }} />
        <div className="dash-top">
          {[0, 1, 2].map(i => <div key={i} className="ui-skeleton" style={{ height: 180 }} />)}
        </div>
      </div>
    );
  }

  const plan = (data.plans || []).find(p => p.period === planTab);

  async function toggle(item) {
    const done = !item.done;
    setData(d => ({
      ...d,
      plans: d.plans.map(p => p.id !== plan.id ? p : {
        ...p,
        items: p.items.map(i => i.id === item.id ? { ...i, done } : i),
      }),
    }));
    try {
      const updated = await toggleStudyPlanItem(plan.id, item.id, done);
      setData(d => ({ ...d, plans: d.plans.map(p => p.id === updated.id ? updated : p) }));
    } catch {
      setData(d => ({
        ...d,
        plans: d.plans.map(p => p.id !== plan.id ? p : {
          ...p, items: p.items.map(i => i.id === item.id ? { ...i, done: !done } : i),
        }),
      }));
    }
  }

  const askTutor = text => navigate(`/app/ai-chat?q=${encodeURIComponent(text)}`);

  return (
    <div className="ui dash">
      <header className="ui-head">
        <div>
          <h1>{greeting()}, {data.user.first_name}</h1>
          <p>{todayLine(data)}</p>
        </div>
        <StreakBadge days={data.streak} longest={data.longest_streak} />
      </header>

      <section className="dash-top">
        <GoalCard today={data.today} />
        <WeekCard week={data.week} />
        <RankCard points={data.points} />
      </section>

      <section className="dash-main">
        <div className="ui-card dash-plan">
          <div className="ui-card-head">
            <h2>O'quv rejam</h2>
            <div className="ui-tabs" role="tablist" aria-label="Reja davri">
              {PERIOD_TABS.map(t => (
                <button key={t.key} role="tab" aria-selected={planTab === t.key}
                  className={planTab === t.key ? "on" : ""} onClick={() => setPlanTab(t.key)}>
                  {t.label}
                  {(data.plans || []).some(p => p.period === t.key) && <span className="dash-dot" aria-hidden="true" />}
                </button>
              ))}
            </div>
          </div>
          {plan ? <PlanView plan={plan} onToggle={toggle} onAsk={askTutor} /> : (
            <div className="dash-plan-empty">
              <p><strong>{PERIOD_TABS.find(t => t.key === planTab)?.label} reja hali yo'q</strong>
                AI Ustoz darajangiz, maqsadingiz va zaif mavzularingizga qarab reja tuzib beradi.</p>
              <button className="ui-btn primary" onClick={() => askTutor(PLAN_PROMPTS[planTab])}>
                AI Ustoz bilan reja tuzish
              </button>
            </div>
          )}
        </div>

        <div className="dash-side">
          <NextCard next={data.next} onAsk={askTutor} />
          <LevelsCard levels={data.levels} onAsk={askTutor} />
        </div>
      </section>

      <section className="dash-learning" aria-label="O'qish ko'rsatkichlari">
        <Metric to="/app/vocabulary" label="O'zlashtirilgan so'zlar" value={data.learning.words_mastered}
          hint={data.learning.words_learning ? `${data.learning.words_learning} tasi o'rganilmoqda` : "Vocabulary bo'limida boshlang"} />
        <Metric to="/app/quiz" label="Quiz o'rtacha natija" value={data.learning.quiz_avg != null ? `${data.learning.quiz_avg}%` : "—"}
          hint={`${data.learning.quizzes_done} ta quiz yechilgan`} />
        <Metric to="/app/vocabulary?tab=cards" label="Flashcard" value={data.learning.cards_mastered}
          hint={data.learning.cards_due ? `${data.learning.cards_due} ta takrorlash kutmoqda` : "yodlangan kartalar"} warn={data.learning.cards_due > 0} />
        <Metric to="/app/ai-chat" label="AI Ustoz darslari" value={data.learning.ai_lessons} hint="tugatilgan darslar" />
      </section>

      <section className="dash-bottom">
        <div className="ui-card">
          <div className="ui-card-head">
            <h2>Faollik</h2>
            <div className="ui-tabs">
              {CHART_PERIODS.map(p => (
                <button key={p.key} className={chartPeriod === p.key ? "on" : ""} onClick={() => setChartPeriod(p.key)}>{p.label}</button>
              ))}
            </div>
          </div>
          <ActivityChart points={data.series?.[chartPeriod] || []} />
        </div>
        <div className="ui-card">
          <div className="ui-card-head"><h2>Oxirgi natijalar</h2></div>
          {data.recent?.length ? (
            <ul className="dash-recent">
              {data.recent.map((r, i) => (
                <li key={i}>
                  <span className="dash-recent-kind">{r.label}</span>
                  <span className="dash-recent-title">{r.title || SUBJECT_LABELS[r.subject] || ""}</span>
                  {r.score != null && <span className={"dash-score" + (r.score >= 70 ? " ok" : r.score < 50 ? " low" : "")}>{r.score}%</span>}
                </li>
              ))}
            </ul>
          ) : <p className="ui-muted">Quiz yoki AI Ustoz bilan dars o'tganingizdan keyin natijalar shu yerda chiqadi.</p>}
        </div>
      </section>
    </div>
  );
}

function todayLine(d) {
  const left = Math.max(0, d.today.goal_minutes - d.today.minutes);
  const order = ["daily", "weekly", "monthly"];
  const plan = [...(d.plans || [])].sort((a, b) => order.indexOf(a.period) - order.indexOf(b.period)).find(p => p.today?.length);
  const todayItems = plan ? plan.items.filter(i => plan.today.includes(i.id)) : [];
  const undone = todayItems.filter(i => !i.done).length;
  if (undone) return plan.period === "monthly"
    ? `Shu haftalik rejada ${undone} ta vazifa qoldi.`
    : `Bugungi rejada ${undone} ta vazifa qoldi.`;
  if (left > 0) return `Kunlik maqsadgacha ${left} daqiqa qoldi.`;
  return "Bugungi maqsad bajarildi. Zo'r ish!";
}

function StreakBadge({ days, longest }) {
  return (
    <div className={"dash-streak" + (days > 0 ? " on" : "")} title={`Eng uzun: ${longest} kun`}>
      <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 2c1 3.5 5 5.5 5 10.5A5 5 0 0 1 7 13c0-2 1-3.5 2-4.5.3 1.6 1.2 2.6 2.2 3C11 8.5 11 5 12 2Z" fill="currentColor" />
      </svg>
      <span><strong>{days}</strong> kunlik seriya</span>
    </div>
  );
}

function GoalCard({ today }) {
  const pct = Math.min(1, today.minutes / Math.max(1, today.goal_minutes));
  const r = 52, c = 2 * Math.PI * r;
  return (
    <div className="ui-card dash-goal">
      <svg viewBox="0 0 120 120" className="dash-ring" role="img" aria-label={`Bugun ${today.minutes} daqiqa, maqsad ${today.goal_minutes}`}>
        <circle cx="60" cy="60" r={r} className="dash-ring-bg" />
        <circle cx="60" cy="60" r={r} className={"dash-ring-fg" + (pct >= 1 ? " done" : "")}
          strokeDasharray={c} strokeDashoffset={c * (1 - pct)} transform="rotate(-90 60 60)" />
        <text x="60" y="58" textAnchor="middle" className="dash-ring-num">{today.minutes}</text>
        <text x="60" y="77" textAnchor="middle" className="dash-ring-sub">/ {today.goal_minutes} daq</text>
      </svg>
      <div>
        <h2>Bugungi maqsad</h2>
        <p className="ui-muted">{pct >= 1 ? "Bajarildi" : `${Math.round(pct * 100)}% bajarildi`}</p>
        <p className="ui-faint">{today.sessions} ta mashq</p>
      </div>
    </div>
  );
}

function WeekCard({ week }) {
  const max = Math.max(15, ...week.days.map(d => d.minutes));
  const todayIso = new Date().toISOString().slice(0, 10);
  return (
    <div className="ui-card dash-week">
      <div className="ui-card-head">
        <h2>Shu hafta</h2>
        <span className="ui-faint">{week.minutes} daq</span>
      </div>
      <div className="dash-week-bars">
        {week.days.map(d => (
          <div key={d.date} className={"dash-week-col" + (d.date === todayIso ? " today" : "")} title={`${d.minutes} daqiqa`}>
            <div className="dash-week-track"><i style={{ height: `${Math.max(d.minutes ? 8 : 0, (d.minutes / max) * 100)}%` }} /></div>
            <span>{d.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function RankCard({ points }) {
  return (
    <Link to="/app/leaderboard" className="ui-card dash-rank">
      <h2>Reyting</h2>
      <div className="dash-rank-num">{points.rank_week ? `${points.rank_week}-o'rin` : "—"}</div>
      <p className="ui-muted">shu hafta · {points.week} ball</p>
      <p className="ui-faint">Umumiy: {points.total} ball{points.rank_all ? `, ${points.rank_all}-o'rin` : ""}</p>
    </Link>
  );
}

function PlanView({ plan, onToggle, onAsk }) {
  const groups = useMemo(() => {
    if (plan.period === "monthly") {
      return [1, 2, 3, 4].map(w => ({
        key: `w${w}`, label: `${w}-hafta`, current: plan.current_week === w,
        items: plan.items.filter(i => i.week === w),
      })).filter(g => g.items.length);
    }
    const byDate = {};
    plan.items.forEach(i => { (byDate[i.date] = byDate[i.date] || []).push(i); });
    const todayIso = new Date().toISOString().slice(0, 10);
    return Object.keys(byDate).sort().map(d => ({
      key: d, label: dayLabel(d), current: d === todayIso, items: byDate[d],
    }));
  }, [plan]);

  return (
    <div>
      <div className="dash-plan-meta">
        <div>
          <strong>{plan.title}</strong>
          <span className="ui-faint"> · {SUBJECT_LABELS[plan.subject_code] || ""} · kuniga {plan.minutes_per_day} daq</span>
        </div>
        <span className="ui-faint">{plan.progress.done}/{plan.progress.total}</span>
      </div>
      <div className="ui-bar ok" style={{ margin: "8px 0 14px" }}><i style={{ width: `${plan.progress.percent}%` }} /></div>
      <div className="dash-plan-groups">
        {groups.map(g => (
          <div key={g.key} className={"dash-plan-group" + (g.current ? " current" : "")}>
            <h3>{g.label}{g.current && <span className="ui-badge accent">{plan.period === "monthly" ? "shu hafta" : "bugun"}</span>}</h3>
            <ul>
              {g.items.map(item => (
                <li key={item.id} className={item.done ? "done" : ""}>
                  <label>
                    <input type="checkbox" checked={!!item.done} onChange={() => onToggle(item)} />
                    <span className="dash-check" aria-hidden="true" />
                    <span className="dash-item-title">{item.title}</span>
                  </label>
                  <span className="dash-item-meta">{TYPE_LABELS[item.type] || item.type} · {item.minutes} daq</span>
                  {!item.done && <Link to={item.link} className="dash-item-go" aria-label={`Boshlash: ${item.title}`}>Boshlash</Link>}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <button className="ui-btn sm" style={{ marginTop: 12 }} onClick={() => onAsk(PLAN_PROMPTS[plan.period].replace("tuzib bering", "qaytadan tuzib bering"))}>
        Rejani yangilash
      </button>
    </div>
  );
}

function dayLabel(iso) {
  const d = new Date(iso + "T00:00:00");
  const names = ["Yakshanba", "Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba"];
  return `${names[d.getDay()]}, ${d.getDate()}.${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function NextCard({ next, onAsk }) {
  const prompt = next.next_step
    ? `Oxirgi darsimdagi keyingi qadamdan davom ettiramiz: ${next.next_step}`
    : next.weak_topics?.length
      ? `Zaif mavzularim bo'yicha dars o'ting: ${next.weak_topics.slice(0, 3).join(", ")}`
      : "Menga darajamga mos dars o'ting.";
  return (
    <div className="ui-card dash-next">
      <h2>Keyingi qadam</h2>
      <p className="dash-next-text">
        {next.next_step || (next.weak_topics?.length ? "Zaif mavzularni mustahkamlash" : "AI Ustoz bilan birinchi darsni boshlang")}
      </p>
      {next.weak_topics?.length > 0 && (
        <div className="ui-chips" style={{ marginBottom: 14 }}>
          {next.weak_topics.map(t => <span key={t} className="ui-badge pen">{t}</span>)}
        </div>
      )}
      <button className="ui-btn ink" onClick={() => onAsk(prompt)}>Darsni boshlash</button>
    </div>
  );
}

function LevelsCard({ levels, onAsk }) {
  return (
    <div className="ui-card">
      <h2 style={{ marginBottom: 12 }}>Darajalarim</h2>
      {levels.length ? (
        <ul className="dash-levels">
          {levels.map(l => (
            <li key={l.subject_code}>
              <span>{SUBJECT_LABELS[l.subject_code] || l.subject_name}</span>
              <strong>{l.level}</strong>
            </li>
          ))}
        </ul>
      ) : (
        <>
          <p className="ui-muted" style={{ marginBottom: 12 }}>Daraja hali aniqlanmagan.</p>
          <button className="ui-btn sm" onClick={() => onAsk("Darajamni aniqlash uchun qisqa test o'tkazing.")}>Daraja testini topshirish</button>
        </>
      )}
    </div>
  );
}

function Metric({ to, label, value, hint, warn }) {
  return (
    <Link to={to} className="ui-card dash-metric">
      <span className="dash-metric-label">{label}</span>
      <span className="dash-metric-value">{value}</span>
      <span className={"dash-metric-hint" + (warn ? " warn" : "")}>{hint}</span>
    </Link>
  );
}

function ActivityChart({ points }) {
  const max = Math.max(10, ...points.map(p => p.minutes));
  const total = points.reduce((a, p) => a + p.minutes, 0);
  if (!total) return <p className="ui-muted">Mashq qilganingiz sari bu yerda grafik paydo bo'ladi.</p>;
  const step = Math.ceil(points.length / 8);
  return (
    <div className="dash-chart" role="img" aria-label={`Jami ${total} daqiqa`}>
      {points.map((p, i) => (
        <div key={p.date} className="dash-chart-col" title={`${p.label}: ${p.minutes} daq`}>
          <div className="dash-chart-track"><i style={{ height: `${(p.minutes / max) * 100}%` }} /></div>
          <span>{i % step === 0 ? p.label : ""}</span>
        </div>
      ))}
    </div>
  );
}
