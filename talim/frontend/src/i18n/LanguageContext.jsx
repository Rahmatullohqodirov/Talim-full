import React, { createContext, useCallback, useContext, useMemo, useState } from "react";
import { TRANSLATIONS, DEFAULT_LANGUAGE, LANGUAGES } from "./translations.js";

const STORAGE_KEY = "talim_lang";

function detectInitialLanguage() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && TRANSLATIONS[saved]) return saved;
  } catch { /* localStorage yo'q — davom etamiz */ }
  return DEFAULT_LANGUAGE;
}

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState(detectInitialLanguage);

  const setLang = useCallback((code) => {
    if (!TRANSLATIONS[code]) return;
    setLangState(code);
    try { localStorage.setItem(STORAGE_KEY, code); } catch { /* e'tiborsiz qoldiramiz */ }
  }, []);

  const t = useCallback((key, fallback) => {
    const dict = TRANSLATIONS[lang] || TRANSLATIONS[DEFAULT_LANGUAGE];
    return dict[key] ?? TRANSLATIONS[DEFAULT_LANGUAGE][key] ?? fallback ?? key;
  }, [lang]);

  const value = useMemo(() => ({ lang, setLang, t, languages: LANGUAGES }), [lang, setLang, t]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage LanguageProvider ichida ishlatilishi kerak");
  return ctx;
}
