import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext.jsx";
import "./Auth.css";

export default function Login() {
  const { login } = useApp();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    if (!username || !password) {
      setError("Login va parolni kiriting");
      return;
    }
    try {
      setError("");
      await login(username, password);
      navigate("/app/dashboard");
    } catch (err) {
      console.error("Login error:", err);
      if (err.message.includes("Failed to fetch") || err.message.includes("NetworkError")) {
        setError("Backendga ulanib bo'lmadi. Server ishga tushganmi va VITE_API_BASE_URL to'g'rimi?");
      } else if (err.message.includes("401") || err.message.includes("400")) {
        setError("Login yoki parol noto'g'ri");
      } else {
        setError("Xatolik: " + err.message);
      }
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-side">
        <div className="auth-brand">Talim</div>
        <div style={{ maxWidth: 420 }}>
          <h1>Avatar bilan real vaqtda til va matematika o'rganing</h1>
          <p style={{ fontSize: 15, lineHeight: 1.6, color: "oklch(0.92 0.02 275)", margin: 0 }}>
            Ingliz, Rus, Nemis, Turk tillari va Matematika — talaffuz, grammatika va yechim qadamlari bo'yicha shaxsiy tahlil bilan.
          </p>
        </div>
        <div className="auth-preview">avatar preview — lip-sync demo video shu yerga qo'yiladi</div>
      </div>
      <div className="auth-form-side">
        <form className="auth-form" onSubmit={handleSubmit}>
          <h2>Xush kelibsiz</h2>
          <p className="sub">Hisobingizga kiring va o'qishni davom ettiring.</p>
          <div className="field">
            <label>Login</label>
            <input className="input" type="text" placeholder="username yoki telefon" value={username} onChange={e => setUsername(e.target.value)} />
          </div>
          <div className="field">
            <label>Parol</label>
            <input className="input" type="password" placeholder="••••••••" value={password} onChange={e => setPassword(e.target.value)} />
          </div>
          {error && <div className="auth-error">{error}</div>}
          <button type="submit" className="btn btn-primary" style={{ width: "100%" }}>Kirish</button>
          <p className="auth-switch">Hisobingiz yo'qmi? <Link to="/register">Ro'yxatdan o'tish</Link></p>
        </form>
      </div>
    </div>
  );
}
