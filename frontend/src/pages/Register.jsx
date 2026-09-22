import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext.jsx";
import "./Auth.css";

export default function Register() {
  const { register } = useApp();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    if (!username || !email || password.length < 8) {
      setError("Barcha maydonlarni to'ldiring, parol kamida 8 belgi");
      return;
    }
    try {
      setError("");
      await register({ username, email, password });
      navigate("/onboarding");
    } catch (err) {
      setError("Ro'yxatdan o'tishda xatolik: ma'lumotlarni tekshiring yoki bu login band");
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-side">
        <div className="auth-brand">Talim</div>
        <div style={{ maxWidth: 420 }}>
          <h1>Avatar bilan real vaqtda til va matematika o'rganing</h1>
          <p style={{ fontSize: 15, lineHeight: 1.6, color: "oklch(0.92 0.02 275)", margin: 0 }}>
            Bir necha soniyada boshlang — bepul.
          </p>
        </div>
        <div className="auth-preview">avatar preview — lip-sync demo video shu yerga qo'yiladi</div>
      </div>
      <div className="auth-form-side">
        <form className="auth-form" onSubmit={handleSubmit}>
          <h2>Hisob yarating</h2>
          <p className="sub">Bir necha soniyada boshlang — bepul.</p>
          <div className="field">
            <label>Ism</label>
            <input className="input" type="text" placeholder="Ismingiz" value={username} onChange={e => setUsername(e.target.value)} />
          </div>
          <div className="field">
            <label>Email</label>
            <input className="input" type="email" placeholder="siz@misol.com" value={email} onChange={e => setEmail(e.target.value)} />
          </div>
          <div className="field">
            <label>Parol</label>
            <input className="input" type="password" placeholder="kamida 8 belgi" value={password} onChange={e => setPassword(e.target.value)} />
          </div>
          {error && <div className="auth-error">{error}</div>}
          <button type="submit" className="btn btn-primary" style={{ width: "100%" }}>Ro'yxatdan o'tish</button>
          <p className="auth-switch">Hisobingiz bormi? <Link to="/login">Kirish</Link></p>
        </form>
      </div>
    </div>
  );
}
