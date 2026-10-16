import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext.jsx";
import { useLanguage } from "../i18n/LanguageContext.jsx";
import PasswordField from "../components/PasswordField.jsx";
import SocialLoginButtons from "../components/SocialLoginButtons.jsx";
import AuthLayout from "../components/AuthLayout.jsx";
import "./Auth.css";

function passwordStrength(p) {
  let s = 0;
  if (p.length >= 8) s++;
  if (p.length >= 12) s++;
  if (/[A-Z]/.test(p) && /[a-z]/.test(p)) s++;
  if (/\d/.test(p)) s++;
  if (/[^A-Za-z0-9]/.test(p)) s++;
  return Math.min(4, s);
}
const STRENGTH = ["Juda kuchsiz", "Kuchsiz", "O'rtacha", "Yaxshi", "Kuchli"];

export default function Register() {
  const { register } = useApp();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const strength = passwordStrength(password);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!name.trim()) return setError("Ismingizni kiriting.");
    if (!/^\S+@\S+\.\S+$/.test(email.trim())) return setError("Email manzilini to'g'ri kiriting.");
    if (password.length < 8) return setError("Parol kamida 8 belgidan iborat bo'lsin.");
    setSubmitting(true);
    setError("");
    try {
      const result = await register({ first_name: name.trim(), email: email.trim().toLowerCase(), password });
      navigate("/verify-email", { state: { email: result.email } });
    } catch (err) {
      const d = err.data || {};
      if (err.isNetworkError) setError("Server bilan aloqa yo'q. Backend ishga tushganini tekshiring.");
      else if (d.email) setError(Array.isArray(d.email) ? d.email[0] : String(d.email));
      else if (d.password) setError("Parol juda oddiy. Boshqa parol tanlang.");
      else setError(err.message || "Ro'yxatdan o'tib bo'lmadi.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout title={t("auth.register.title")} subtitle={t("auth.register.subtitle")}>
      <form onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label htmlFor="reg-name">{t("auth.register.name_label")}</label>
          <input id="reg-name" className="input" type="text" autoComplete="given-name" placeholder={t("auth.register.name_placeholder")}
            value={name} onChange={e => setName(e.target.value)} autoFocus />
        </div>
        <div className="field">
          <label htmlFor="reg-email">{t("auth.register.email_label")}</label>
          <input id="reg-email" className="input" type="email" autoComplete="email" placeholder="siz@misol.com"
            value={email} onChange={e => setEmail(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="reg-pass">{t("auth.password_label")}</label>
          <PasswordField id="reg-pass" autoComplete="new-password" value={password} onChange={e => setPassword(e.target.value)} placeholder={t("auth.register.password_placeholder")} />
          {password && (
            <div className={`auth-strength s${strength}`} aria-live="polite">
              <span><i /><i /><i /><i /></span>{STRENGTH[strength]}
            </div>
          )}
        </div>
        {error && <div className="auth-error" role="alert">{error}</div>}
        <button type="submit" className="auth-submit" disabled={submitting}>{submitting ? t("auth.register.submit_busy") : t("auth.register.submit")}</button>
      </form>
      <SocialLoginButtons onError={setError} />
      <p className="auth-switch">{t("auth.register.switch_text")} <Link to="/login">{t("auth.register.switch_link")}</Link></p>
    </AuthLayout>
  );
}
