import React from "react";
import { Link } from "react-router-dom";

/** Kirish / ro'yxatdan o'tish / email tasdiqlash sahifalari uchun umumiy tuzilma. */
export default function AuthLayout({ title, subtitle, children, aside }) {
  return (
    <div className="auth">
      <aside className="auth-show" aria-hidden="true">
        <Link to="/" className="auth-logo">Talim</Link>
        <div className="auth-show-main">
          <h1>{aside?.title || "Shaxsiy AI ustoz bilan tillar va matematika"}</h1>
          <p>{aside?.text || "Ingliz, rus, nemis, turk tillari va matematika. Ustoz darajangizni aniqlaydi, reja tuzadi va xatolaringizni eslab qoladi."}</p>
          <div className="auth-demo">
            <div className="auth-demo-msg me">I go to park yesterday</div>
            <div className="auth-demo-msg ai">
              Zo'r urinish! Faqat o'tgan zamon kerak.
              <div className="auth-demo-note">
                <b>I go</b> → <b>I went</b> · <b>park</b> → <b>the park</b>
              </div>
            </div>
          </div>
        </div>
        <ul className="auth-facts">
          <li><strong>6</strong> fan</li>
          <li><strong>9 700+</strong> so'z</li>
          <li><strong>A1–C2</strong> darajalar</li>
        </ul>
      </aside>
      <main className="auth-panel">
        <div className="auth-card">
          <Link to="/" className="auth-logo mobile">Talim</Link>
          <h2>{title}</h2>
          {subtitle && <p className="auth-sub">{subtitle}</p>}
          {children}
        </div>
      </main>
    </div>
  );
}
