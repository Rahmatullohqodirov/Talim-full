import React, { useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { useApp } from "../context/AppContext.jsx";
import AuthLayout from "../components/AuthLayout.jsx";
import "./Auth.css";

export default function VerifyEmail() {
  const { verifyEmail, resendCode } = useApp();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState(location.state?.email || "");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!email || code.length !== 6) {
      setError("Email va 6 xonali kodni to'liq kiriting");
      return;
    }
    setSubmitting(true);
    try {
      setError("");
      await verifyEmail(email, code);
      navigate("/onboarding");
    } catch (err) {
      setError(err.message.includes("400") ? "Kod noto'g'ri yoki muddati tugagan" : "Xatolik: " + err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResend() {
    if (!email || resendCooldown > 0) return;
    setInfo("");
    setError("");
    try {
      await resendCode(email);
      setInfo("Agar bu email ro'yxatdan o'tgan bo'lsa, yangi kod yuborildi.");
      setResendCooldown(60);
      const timer = setInterval(() => {
        setResendCooldown(c => {
          if (c <= 1) { clearInterval(timer); return 0; }
          return c - 1;
        });
      }, 1000);
    } catch {
      setError("Kod qayta yuborilmadi. Birozdan so'ng urinib ko'ring.");
    }
  }

  return (
    <AuthLayout title="Emailni tasdiqlang" subtitle={null}
      aside={{ title: "Deyarli tayyor!", text: "Emailni tasdiqlash hisobingizni begona odamlardan himoya qiladi." }}>
        <form onSubmit={handleSubmit}>
          <p className="auth-sub">
            <strong>{email || "emailingiz"}</strong> manziliga 6 xonali kod yubordik.
            Kodni quyida kiriting. Xat kelmasa, "Spam" papkasini tekshiring.
          </p>
          {!location.state?.email && (
            <div className="field">
              <label>Email</label>
              <input className="input" type="email" placeholder="siz@misol.com" value={email} onChange={e => setEmail(e.target.value)} />
            </div>
          )}
          <div className="field">
            <label>Tasdiqlash kodi</label>
            <input
              className="verify-code-input"
              inputMode="numeric"
              maxLength={6}
              placeholder="000000"
              value={code}
              onChange={e => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
            />
          </div>
          {error && <div className="auth-error">{error}</div>}
          {info && <div className="auth-hint" style={{ color: "oklch(0.55 0.15 155)" }}>{info}</div>}
          <button type="submit" className="auth-submit" disabled={submitting || code.length < 6}>
            {submitting ? "Tekshirilmoqda..." : "Tasdiqlash"}
          </button>
          <p className="auth-hint">
            Kod kelmadimi?{" "}
            <button type="button" className="auth-resend-btn" onClick={handleResend} disabled={resendCooldown > 0}>
              {resendCooldown > 0 ? `Qayta yuborish (${resendCooldown}s)` : "Qayta yuborish"}
            </button>
          </p>
          <p className="auth-switch"><Link to="/login">Kirish sahifasiga qaytish</Link></p>
        </form>
    </AuthLayout>
  );
}
