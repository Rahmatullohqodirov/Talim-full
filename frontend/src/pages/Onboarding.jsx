import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { updateProfile } from "../api/client.js";
import "./Onboarding.css";

const GOALS = [
  { id: "learn", icon: "🎓", title: "Bilim olish", desc: "Kurslar, darslar, testlar va video materiallar orqali bilim oling." },
  { id: "teach", icon: "💬", title: "Dars berish", desc: "O'quvchilarga dars bering, kurslar yarating va bilim ulashing." },
  { id: "manage_center", icon: "🏛️", title: "Ta'lim markazini boshqarish", desc: "O'qituvchilar, o'quvchilar va kurslarni boshqaring." },
  { id: "team", icon: "👥", title: "Jamoa bilan ishlash", desc: "Chat, guruhlar va hamkorlik vositalari orqali ishlang." },
  { id: "channel", icon: "📣", title: "Kanal yaratish", desc: "O'z kanalingizni oching va auditoriyangiz bilan bog'laning." },
  { id: "meeting", icon: "🎥", title: "Meeting o'tkazish", desc: "Onlayn darslar, uchrashuv va videokonferensiyalar o'tkazing." },
  { id: "video", icon: "▶️", title: "Video darslar joylash", desc: "Video kontent joylang va keng auditoriyaga yetkazing." },
  { id: "company", icon: "💼", title: "Kompaniya uchun muhit yaratish", desc: "Kompaniyangiz uchun alohida workspace yarating." },
];

const GOALS_WIDE = [
  { id: "project", icon: "</>", title: "Loyiha ustida ishlash", desc: "Dasturiy loyihalar, fayllar va vazifalarni boshqaring." },
  { id: "explore", icon: "🔍", title: "Shunchaki tanishib chiqish", desc: "Platformani ko'rib chiqing va imkoniyatlarini o'rganing." },
];

const ROLES = [
  { id: "student", icon: "🧑‍🎓", label: "O'quvchi" },
  { id: "teacher", icon: "🧑‍🏫", label: "O'qituvchi" },
  { id: "admin", icon: "🛠️", label: "Administrator" },
  { id: "center", icon: "🏛️", label: "Ta'lim markazi" },
  { id: "company", icon: "🏢", label: "Kompaniya" },
  { id: "dev", icon: "💻", label: "Dasturchi" },
  { id: "other", icon: "❓", label: "Boshqa" },
];

const STEPS = ["welcome", "goal", "role", "done"];

function isDesktopViewport() {
  return typeof window !== "undefined" && window.innerWidth > 860;
}

export default function Onboarding() {
  const navigate = useNavigate();
  const [step, setStep] = useState(isDesktopViewport() ? "goal" : "welcome");
  const [goal, setGoal] = useState("learn");
  const [role, setRole] = useState("student");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    function onResize() {
      if (isDesktopViewport() && step === "welcome") setStep("goal");
    }
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [step]);

  const stepIndex = STEPS.indexOf(step);

  function goBack() {
    if (stepIndex > 0) setStep(STEPS[stepIndex - 1]);
  }

  async function finish() {
    setSaving(true);
    try {
      await updateProfile({ onboarding_goal: goal, onboarding_role: role, onboarding_completed: true });
    } catch (e) { /* offline/demo — davom etamiz */ }
    localStorage.setItem("st_onboarding", JSON.stringify({ goal, role, completedAt: Date.now() }));
    navigate("/app/dashboard", { replace: true });
  }

  return (
    <div className="onb-wrap">
      <div className="onb-side">
        <div className="onb-side-top">
          <div className="onb-logo-mark" />
          <div>
            <div className="onb-brand">Talim</div>
            <div className="onb-tagline">Ta'lim. Aloqa. Rivojlanish.</div>
          </div>
        </div>
        <div className="onb-side-body">
          <h1>Talim'ga xush kelibsiz!</h1>
          <p>Talim — ta'lim, aloqa va hamkorlik uchun yaratilgan zamonaviy platforma. O'z maqsadingizga mos tarzda foydalanishni boshlang.</p>
          <div className="onb-illustration">optima illustratsiyasi</div>
        </div>
        <div className="onb-dots">
          {STEPS.map((s, i) => <div key={s} className={"onb-dot" + (i === stepIndex ? " active" : "")} />)}
        </div>
      </div>

      <div className="onb-main">
        <div className="onb-topbar">
          {stepIndex > 0 && step !== "done" && (
            <button className="onb-back" onClick={goBack} type="button" aria-label="Orqaga">←</button>
          )}
          <div style={{ flex: 1 }} />
          {step !== "done" && <div className="onb-lang">🌐 O'zbekcha ⌄</div>}
        </div>

        <div className="onb-content">

          {step === "welcome" && (
            <div className="onb-welcome-mobile">
              <div className="onb-illustration">optima illustratsiyasi</div>
              <h2>Talim'ga xush kelibsiz!</h2>
              <p className="onb-sub">Talim — ta'lim, aloqa va hamkorlik uchun yaratilgan zamonaviy platforma.</p>
              <button className="btn btn-primary onb-next" onClick={() => setStep("goal")} type="button">Boshlash</button>
            </div>
          )}

          {step === "goal" && (
            <>
              <h2>Platformadan qanday maqsadda foydalanmoqchisiz?</h2>
              <p className="onb-sub">Siz tanlagan maqsadga qarab, Talim sizga mos muhitni tayyorlaydi.</p>
              <div className="onb-grid">
                {GOALS.map(g => (
                  <button key={g.id} className={"onb-card" + (goal === g.id ? " selected" : "")} onClick={() => setGoal(g.id)} type="button">
                    {goal === g.id && <span className="onb-check">✓</span>}
                    <div className="onb-card-icon">{g.icon}</div>
                    <div className="onb-card-title">{g.title}</div>
                    <div className="onb-card-desc">{g.desc}</div>
                    <span className="onb-chevron">›</span>
                  </button>
                ))}
              </div>
              <div className="onb-grid onb-grid-wide">
                {GOALS_WIDE.map(g => (
                  <button key={g.id} className={"onb-card onb-card-wide" + (goal === g.id ? " selected" : "")} onClick={() => setGoal(g.id)} type="button">
                    {goal === g.id && <span className="onb-check">✓</span>}
                    <div className="onb-card-icon">{g.icon}</div>
                    <div>
                      <div className="onb-card-title">{g.title}</div>
                      <div className="onb-card-desc">{g.desc}</div>
                    </div>
                    <span className="onb-chevron">›</span>
                  </button>
                ))}
              </div>
              <div className="onb-lock">🔒 Siz yaratgan ma'lumotlar xavfsiz va maxfiy saqlanadi.</div>
              <div className="onb-actions">
                <button className="btn btn-primary onb-next" onClick={() => setStep("role")} type="button">Davom etish</button>
              </div>
            </>
          )}

          {step === "role" && (
            <>
              <h2>Sizning rolingiz kim?</h2>
              <p className="onb-sub">Sizni eng yaxshi tajriba bilan ta'minlashimiz uchun tanlang.</p>
              <div className="onb-list">
                {ROLES.map(r => (
                  <button key={r.id} className={"onb-row" + (role === r.id ? " selected" : "")} onClick={() => setRole(r.id)} type="button">
                    <span className="onb-row-icon">{r.icon}</span>
                    <span className="onb-row-title">{r.label}</span>
                    <span className="onb-radio" />
                  </button>
                ))}
              </div>
              <div className="onb-actions">
                <button className="btn btn-outline onb-back-desktop" onClick={goBack} type="button">Orqaga</button>
                <button className="btn btn-primary onb-next" onClick={() => setStep("done")} type="button">Davom etish</button>
              </div>
              <div className="onb-lock">🔒 Siz yaratgan ma'lumotlar xavfsiz va maxfiy saqlanadi.</div>
            </>
          )}

          {step === "done" && (
            <div className="onb-done">
              <div className="onb-done-badge">✓</div>
              <h2>Tayyor!</h2>
              <p className="onb-sub" style={{ textAlign: "center" }}>Sizga mos muhit tayyorlandi. Talim'da samarali va maroqli foydalaning!</p>
              <button className="btn btn-primary onb-next" onClick={finish} disabled={saving} type="button">
                {saving ? "..." : "Talim'ga kirish"}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
