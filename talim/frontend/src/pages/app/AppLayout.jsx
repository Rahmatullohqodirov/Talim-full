import React from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useApp } from "../../context/AppContext.jsx";
import { useLanguage } from "../../i18n/LanguageContext.jsx";
import StatusPill from "../../components/StatusPill.jsx";
import "./App.css";

const studentNav = [
  { groupKey: "nav.group.reading" },
  { to: "dashboard", labelKey: "nav.dashboard", dot: "oklch(0.6 0.15 275)" },
  { to: "ai-chat", labelKey: "nav.ai_teacher", dot: "oklch(0.6 0.15 275)" },
  { to: "chat", labelKey: "nav.avatar_chat", dot: "oklch(0.65 0.15 200)" },
  { groupKey: "nav.group.practice" },
  { to: "lessons", labelKey: "nav.lessons", dot: "oklch(0.6 0.18 300)" },
  { to: "vocabulary", labelKey: "nav.words", dot: "oklch(0.65 0.18 50)" },
  { to: "quiz", labelKey: "nav.quiz", dot: "oklch(0.6 0.18 300)" },
  { to: "math", labelKey: "nav.math", dot: "oklch(0.7 0.15 85)" },
  { groupKey: "nav.group.resources" },
  { to: "dictionary", labelKey: "nav.dictionary", dot: "oklch(0.6 0.14 155)" },
  { to: "videos", labelKey: "nav.videos", dot: "oklch(0.65 0.18 25)" },
  { to: "courses", labelKey: "nav.courses", dot: "oklch(0.6 0.15 155)" },
  { groupKey: "nav.group.me" },
  { to: "profile", labelKey: "nav.profile", dot: "oklch(0.6 0.15 275)" },
  { to: "leaderboard", labelKey: "nav.leaderboard", dot: "oklch(0.65 0.18 25)" },
  { to: "billing", labelKey: "nav.billing", dot: "oklch(0.7 0.15 85)" },
];

export default function AppLayout() {
  const { role, logout } = useApp();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const { pathname } = useLocation();

  function handleLogout() {
    logout();
    navigate("/");
  }

  // Admin panelning o'z menyusi bor — ikkinchi (bo'sh) sidebar ko'rsatilmaydi
  if (role === "admin" && pathname.startsWith("/app/admin")) return <Outlet />;

  return (
    <div className="app-shell">
      <div className="sidebar">
        <div className="sidebar-brand">Talim</div>

        {role === "admin" ? (
          <NavLink
            to="admin"
            className={({ isActive }) =>
              "nav-item" + (isActive ? " active" : "")
            }
          >
            <span
              className="nav-dot"
              style={{ background: "oklch(0.7 0.15 275)" }}
            />
            <span>Admin panel</span>
          </NavLink>
        ) : (
          studentNav.map((n) => n.groupKey ? (
            <div key={n.groupKey} className="nav-group">{t(n.groupKey)}</div>
          ) : (
            <NavLink
              key={n.to}
              to={n.to}
              className={({ isActive }) =>
                "nav-item" + (isActive ? " active" : "")
              }
            >
              <span
                className="nav-dot"
                style={{ background: n.dot }}
              />
              <span>{t(n.labelKey)}</span>
            </NavLink>
          ))
        )}

        <div style={{ flex: 1 }} />

        <div style={{ padding: "0 12px 12px" }}>
          <StatusPill />
        </div>

        <div
          className="logout-item"
          onClick={handleLogout}
        >
          {t("common.logout")}
        </div>
      </div>

      <div className="content">
        <Outlet />
      </div>
    </div>
  );
}