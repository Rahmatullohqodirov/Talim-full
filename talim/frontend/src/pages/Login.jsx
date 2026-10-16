import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext.jsx";
import { useLanguage } from "../i18n/LanguageContext.jsx";
import PasswordField from "../components/PasswordField.jsx";
import SocialLoginButtons from "../components/SocialLoginButtons.jsx";
import AuthLayout from "../components/AuthLayout.jsx";
import "./Auth.css";

export default function Login() {
  const { login } = useApp();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError("Email (yoki login) va parolni kiriting.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await login(username.trim(), password);
      navigate("/app/dashboard");
    } catch (err) {
      if (err.data?.code === "email_not_verified") {
        navigate("/verify-email", { state: { email: err.data.email } });
      } else if (err.isNetworkError) {
        setError("Server bilan aloqa yo'q. Backend ishga tushganini tekshiring.");
      } else if (err.status === 429) {
        setError("Juda ko'p urinish. Bir daqiqadan keyin qayta urinib ko'ring.");
      } else {
        setError("Email yoki parol noto'g'ri.");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthLayout title={t("auth.login.title")} subtitle={t("auth.login.subtitle")}>
      <form onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label htmlFor="login-id">{t("auth.login.id_label")}</label>
          <input id="login-id" className="input" type="text" autoComplete="username" placeholder="siz@misol.com"
            value={username} onChange={e => setUsername(e.target.value)} autoFocus />
        </div>
        <div className="field">
          <label htmlFor="login-pass">{t("auth.password_label")}</label>
          <PasswordField id="login-pass" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" />
        </div>
        {error && <div className="auth-error" role="alert">{error}</div>}
        <button type="submit" className="auth-submit" disabled={busy}>{busy ? t("auth.login.submit_busy") : t("auth.login.submit")}</button>
      </form>
      <SocialLoginButtons onError={setError} />
      <p className="auth-switch">{t("auth.login.switch_text")} <Link to="/register">{t("auth.login.switch_link")}</Link></p>
    </AuthLayout>
  );
}
