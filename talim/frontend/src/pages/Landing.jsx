import React from "react";
import { Link } from "react-router-dom";
import { useLanguage } from "../i18n/LanguageContext.jsx";
import "./Landing.css";

export default function Landing() {
  const { t } = useLanguage();

  const dockItems = [
    { icon: "⌘", label: t("dock.home"), href: "#", active: true },
    { icon: "◈", label: t("dock.chat"), href: "#features", active: false },
    { icon: "∑", label: t("dock.math"), href: "#features", active: false },
    { icon: "▶", label: t("dock.videos"), href: "#features", active: false },
    { icon: "▤", label: t("dock.stats"), href: "#features", active: false },
    { icon: "⌘", label: t("dock.pricing"), href: "#pricing", active: false },
  ];

  const featureCards = [1, 2, 3, 4, 5, 6, 7, 8].map(n => ({
    icon: ["🗣️", "📊", "🌐", "∫", "🔁", "🏆", "▶", "💬"][n - 1],
    title: t(`feature.${n}.title`),
    desc: t(`feature.${n}.desc`),
  }));

  const steps = [1, 2, 3].map(n => ({
    n: `0${n}`,
    title: t(`steps.${n}.title`),
    desc: t(`steps.${n}.desc`),
  }));

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
            <a href="#features">{t("nav.features")}</a>
            <a href="#pricing">{t("nav.pricing")}</a>
            <a href="#faq">{t("nav.faq")}</a>
          </div>
          <Link to="/login" className="gold-btn">{t("nav.login")}</Link>
        </nav>

        <div className="hero">
          <div className="eyebrow"><span style={{ width: 6, height: 6, borderRadius: "50%", background: "oklch(0.75 0.16 85)" }} />{t("hero.eyebrow")}</div>
          <h1>
            <span style={{ color: "white" }}>{t("hero.title1")}</span><br />
            <span className="hero-gradient-text">{t("hero.title2")}</span>
          </h1>
          <p className="lead">{t("hero.lead")}</p>
          <div className="hero-actions">
            <Link to="/register" className="gold-btn" style={{ padding: "15px 32px", fontSize: 14.5 }}>{t("hero.cta_start")}</Link>
            <a href="#features" className="ghost-btn">{t("hero.cta_how")}</a>
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
          <div className="section-eyebrow">{t("features.eyebrow")}</div>
          <h2 className="section-title">{t("features.title")}</h2>
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
          <div className="section-eyebrow">{t("pricing.eyebrow")}</div>
          <h2 className="section-title" style={{ fontSize: 34 }}>{t("pricing.title")}</h2>
        </div>
        <div className="plans-grid">
          <div className="plan-card free">
            <div className="plan-name">{t("plan.free.name")}</div>
            <div className="plan-price">$0<span> /oy</span></div>
            {[t("plan.free.f1"), t("plan.free.f2"), t("plan.free.f3"), t("plan.free.f4")].map((ft, i) => (
              <div key={i} className="plan-feature"><span style={{ color: "oklch(0.75 0.16 85)" }}>✓</span>{ft}</div>
            ))}
            <Link to="/register" className="plan-btn ghost">{t("plan.free.cta")}</Link>
          </div>
          <div className="plan-card premium">
            <div className="plan-name">{t("plan.premium.name")}</div>
            <div className="plan-price">$9<span> /oy</span></div>
            {[t("plan.premium.f1"), t("plan.premium.f2"), t("plan.premium.f3"), t("plan.premium.f4")].map((ft, i) => (
              <div key={i} className="plan-feature"><span style={{ color: "oklch(0.75 0.16 85)" }}>✓</span>{ft}</div>
            ))}
            <Link to="/register" className="plan-btn gold">{t("plan.premium.cta")}</Link>
          </div>
        </div>
      </div>

      <div className="cta-band">
        <h2>{t("cta.title")}</h2>
        <p style={{ color: "oklch(0.85 0.02 85)", fontSize: 15, margin: "0 0 32px" }}>{t("cta.sub")}</p>
        <Link to="/register" className="gold-btn" style={{ padding: "16px 36px", fontSize: 15 }}>{t("cta.button")}</Link>
      </div>

      <div className="landing-footer">
        <div style={{ fontFamily: "var(--font-display)", fontWeight: 800, color: "oklch(0.85 0.02 85)" }}>OPTIMA</div>
        <div>&copy; 2026 Talim. {t("footer.rights")}</div>
      </div>
    </div>
  );
}
