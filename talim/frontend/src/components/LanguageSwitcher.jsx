import React, { useEffect, useRef, useState } from "react";
import { useLanguage } from "../i18n/LanguageContext.jsx";
import "./LanguageSwitcher.css";

/** Sayt burchagidagi til tanlagich — barcha sahifalarda (ochiq va ichki) ko'rinadi. */
export default function LanguageSwitcher() {
  const { lang, setLang, t, languages } = useLanguage();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const current = languages.find(l => l.code === lang) || languages[0];

  useEffect(() => {
    function onDocClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  return (
    <div className="lang-switcher" ref={ref}>
      <button
        type="button"
        className="lang-switcher-btn"
        onClick={() => setOpen(o => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
        title={t("language.switcher_label")}
      >
        <span className="lang-flag">{current.flag}</span>
        <span className="lang-code">{current.code.toUpperCase()}</span>
        <span className="lang-caret">▾</span>
      </button>
      {open && (
        <ul className="lang-menu" role="listbox">
          {languages.map(l => (
            <li key={l.code}>
              <button
                type="button"
                className={"lang-option" + (l.code === lang ? " on" : "")}
                onClick={() => { setLang(l.code); setOpen(false); }}
                role="option"
                aria-selected={l.code === lang}
              >
                <span className="lang-flag">{l.flag}</span>
                <span>{l.label}</span>
                {l.code === lang && <span className="lang-check">✓</span>}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
