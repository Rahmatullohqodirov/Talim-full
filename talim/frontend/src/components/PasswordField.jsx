import React, { useState } from "react";

export default function PasswordField({ value, onChange, placeholder, id, autoComplete }) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="field-password-wrap">
      <input
        className="input"
        id={id}
        autoComplete={autoComplete}
        type={visible ? "text" : "password"}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
      />
      <button
        type="button"
        className="field-password-toggle"
        onClick={() => setVisible(v => !v)}
        aria-label={visible ? "Parolni yashirish" : "Parolni ko'rsatish"}
        tabIndex={-1}
      >
        {visible ? <EyeOffIcon /> : <EyeIcon />}
      </button>
    </div>
  );
}

function EyeIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  );
}

function EyeOffIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M3 3l18 18M10.6 10.6a3 3 0 004.24 4.24M9.9 4.24A11 11 0 0112 4c7 0 11 7 11 7a13.5 13.5 0 01-3.13 3.87M6.5 6.5C4 8.1 2.4 10.4 1 12c0 0 4 7 11 7 1.4 0 2.7-.27 3.9-.75" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}
