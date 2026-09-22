import React from "react";
import { Link } from "react-router-dom";
import "./Landing.css";

const dockItems = [
  { icon: "⌘", label: "ASOSIY", href: "#", active: true },
  { icon: "◈", label: "SUHBAT", href: "#features", active: false },
  { icon: "∑", label: "MATEMATIKA", href: "#features", active: false },
  { icon: "▶", label: "VIDEOLAR", href: "#features", active: false },
  { icon: "▤", label: "STATISTIKA", href: "#features", active: false },
  { icon: "⌘", label: "NARXLAR", href: "#pricing", active: false },
];

const featureCards = [
  { icon: "🗣️", title: "Real-time avatar suhbat", desc: "Lip-sync avatar bilan ovozli muloqot, talaffuz va grammatika bo'yicha darhol fikr-mulohaza." },
  { icon: "📊", title: "Chuqur statistika", desc: "Har fan bo'yicha vaqt, daraja o'sishi, streak va heatmap — bitta dashboardda." },
  { icon: "🌐", title: "5 fan, bitta ilova", desc: "Ingliz, Rus, Nemis, Turk tillari va Matematika — CEFR darajalari bo'yicha tuzilgan." },
  { icon: "∫", title: "Matematika + SymPy", desc: "Bosqichma-bosqich yechim, grafiklar va zaif mavzular tahlili." },
  { icon: "🔁", title: "Spaced repetition", desc: "Flashcard va quiz orqali bilimni uzoq muddat mustahkamlash." },
  { icon: "🏆", title: "Motivatsiya tizimi", desc: "Streak, haftalik hisobot va do'stlar bilan leaderboard." },
  { icon: "▶", title: "AI video tavsiyalari", desc: "Har darsdan keyin AI zaif mavzungizga mos YouTube videolarini tanlab beradi." },
  { icon: "💬", title: "AI Chat repetitor", desc: "Har qanday savolga darhol javob beruvchi shaxsiy AI yordamchi." },
];

const steps = [
  { n: "01", title: "Ro'yxatdan o'ting", desc: "Fan va darajangizni tanlang — 30 soniyada tayyor." },
  { n: "02", title: "Avatar bilan suhbatlashing", desc: "Real vaqtda gapiring, avatar tinglaydi va tuzatadi." },
  { n: "03", title: "Progressni kuzating", desc: "Statistikangiz avtomatik yangilanadi, zaif joylar aniqlanadi." },
];

export default function Landing() {
  return (
    <div className="landing">
      <div style={{ position: "relative" }}>
        <div className="blob" style={{ top: -120, left: -80, width: 480, height: 480, background: "oklch(0.55 0.19 55 / 0.55)", animation: "drift1 14s ease-in-out infinite" }} />
        <div className="blob" style={{ top: 80, right: -120, width: 520, height: 520, background: "oklch(0.6 0.17 40 / 0.45)", animation: "drift2 16s ease-in-out infinite" }} />
        <div className="blob" style={{ top: 340, left: "40%", width: 380, height: 380, background: "oklch(0.7 0.15 85 / 0.3)", animation: "drift1 18s ease-in-out infinite reverse" }} />

        <nav className="landing-nav">
          <div className="brand">
            <div className="brand-mark">
              <div style={{ position: "absolute", width: 18, height: 18, background: "linear-gradient(135deg, oklch(0.85 0.15 85), oklch(0.65 0.18 55))", borderRadius: 5, transform: "rotate(45deg)", top: 0, left: 6 }} />
              <div style={{ position: "absolute", width: 14, height: 14, background: "oklch(0.4 0.05 50)", borderRadius: 4, transform: "rotate(45deg)", bottom: 0, left: 0 }} />
              <div style={{ position: "absolute", width: 14, height: 14, background: "oklch(0.4 0.05 50)", borderRadius: 4, transform: "rotate(45deg)", bottom: 0, right: 0 }} />
            </div>
            <div style={{ fontFamily: "var(--font-display)", fontWeight: 800, fontSize: 15, letterSpacing: "0.04em" }}>TALIM</div>
          </div>
          <div className="nav-links">
            <a href="#features">IMKONIYATLAR</a>
            <a href="#pricing">NARXLAR</a>
            <a href="#faq">SAVOLLAR</a>
          </div>
          <Link to="/login" className="gold-btn">KIRISH</Link>
        </nav>

        <div className="hero">
          <div className="eyebrow"><span style={{ width: 6, height: 6, borderRadius: "50%", background: "oklch(0.75 0.16 85)" }} />KELAJAK — Talim</div>
          <h1>
            <span style={{ color: "white" }}>TIL VA MATNNI</span><br />
            <span className="hero-gradient-text">AVATAR BILAN O'RGANING</span>
          </h1>
          <p className="lead">Ingliz, Rus, Nemis, Turk tillari va Matematika — real-time ovozli suhbat, talaffuz tahlili va shaxsiy statistika bilan.</p>
          <div className="hero-actions">
            <Link to="/register" className="gold-btn" style={{ padding: "15px 32px", fontSize: 14.5 }}>Bepul boshlash</Link>
            <a href="#features" className="ghost-btn">Qanday ishlaydi</a>
          </div>
          <div className="dock">
            {dockItems.map((d, i) => (
              <a key={i} href={d.href} className={"dock-item" + (d.active ? " active" : "")}>
                <span style={{ fontSize: 18 }}>{d.icon}</span>
                <span style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: "0.04em" }}>{d.label}</span>
              </a>
            ))}
          </div>
        </div>
      </div>

      <div id="features" className="section" style={{ paddingTop: 140 }}>
        <div className="section-head">
          <div className="section-eyebrow">IMKONIYATLAR</div>
          <h2 className="section-title">Bitta ilovada o'qituvchi, tahlilchi va motivator</h2>
        </div>
        <div className="feature-grid">
          {featureCards.map((f, i) => (
            <div key={i} className="card">
              <div className="card-icon">{f.icon}</div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="section">
        <div className="steps-box">
          {steps.map((st, i) => (
            <div key={i}>
              <div className="step-num">{st.n}</div>
              <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 8 }}>{st.title}</div>
              <div style={{ fontSize: 13.5, lineHeight: 1.6, color: "oklch(0.72 0.02 85)" }}>{st.desc}</div>
            </div>
          ))}
        </div>
      </div>

      <div id="pricing" className="section">
        <div className="section-head" style={{ marginBottom: 48 }}>
          <div className="section-eyebrow">NARXLAR</div>
          <h2 className="section-title" style={{ fontSize: 34 }}>Bepul boshlang, xohlasangiz kengaytiring</h2>
        </div>
        <div className="plans-grid">
          <div className="plan-card free">
            <div className="plan-name">Free</div>
            <div className="plan-price">$0<span> /oy</span></div>
            {["Ingliz + Matematika", "Kunlik 15 daq suhbat", "Asosiy statistika", "1 ta avatar"].map((ft, i) => (
              <div key={i} className="plan-feature"><span style={{ color: "oklch(0.75 0.16 85)" }}>✓</span>{ft}</div>
            ))}
            <Link to="/register" className="plan-btn ghost">Bepul boshlash</Link>
          </div>
          <div className="plan-card premium">
            <div className="plan-name">Premium</div>
            <div className="plan-price">$9<span> /oy</span></div>
            {["Barcha 5 fan", "Cheksiz suhbat", "To'liq statistika + PDF", "Voice cloning"].map((ft, i) => (
              <div key={i} className="plan-feature"><span style={{ color: "oklch(0.75 0.16 85)" }}>✓</span>{ft}</div>
            ))}
            <Link to="/register" className="plan-btn gold">Premium'ga o'tish</Link>
          </div>
        </div>
      </div>

      <div className="cta-band">
        <h2>O'rganishni bugun boshlang</h2>
        <p style={{ color: "oklch(0.85 0.02 85)", fontSize: 15, margin: "0 0 32px" }}>Ro'yxatdan o'tish 30 soniya vaqt oladi.</p>
        <Link to="/register" className="gold-btn" style={{ padding: "16px 36px", fontSize: 15 }}>Bepul hisob yaratish</Link>
      </div>

      <div className="landing-footer">
        <div style={{ fontFamily: "var(--font-display)", fontWeight: 800, color: "oklch(0.85 0.02 85)" }}>OPTIMA</div>
        <div>&copy; 2026 Talim. Barcha huquqlar himoyalangan.</div>
      </div>
    </div>
  );
}
