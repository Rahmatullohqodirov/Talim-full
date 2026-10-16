import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  fetchAccount, updateAccount, changePassword, fetchDashboard,
  fetchAvatars, fetchMe, updateProfile, fetchSubscriptionStatus,
} from "../../api/client.js";
import { useLanguage } from "../../i18n/LanguageContext.jsx";
import "./ui.css";
import "./Profile.css";

export default function Profile() {
  const { t, lang, setLang, languages } = useLanguage();

  const [account, setAccount] = useState(null);
  const [accountForm, setAccountForm] = useState({ first_name: "", last_name: "", email: "" });
  const [accountMsg, setAccountMsg] = useState(null);
  const [accountBusy, setAccountBusy] = useState(false);

  const [pwForm, setPwForm] = useState({ old_password: "", new_password: "", confirm: "" });
  const [pwMsg, setPwMsg] = useState(null);
  const [pwBusy, setPwBusy] = useState(false);

  const [dashboard, setDashboard] = useState(null);
  const [avatars, setAvatars] = useState(null);
  const [me, setMe] = useState(null);
  const [avatarBusy, setAvatarBusy] = useState(false);
  const [status, setStatus] = useState(null);

  function loadAccount() {
    fetchAccount().then(a => {
      setAccount(a);
      setAccountForm({ first_name: a.first_name || "", last_name: a.last_name || "", email: a.email || "" });
    }).catch(() => {});
  }

  useEffect(() => {
    loadAccount();
    fetchDashboard().then(setDashboard).catch(() => {});
    fetchAvatars().then(d => setAvatars(Array.isArray(d) ? d : d?.results || [])).catch(() => {});
    fetchMe().then(setMe).catch(() => {});
    fetchSubscriptionStatus().then(setStatus).catch(() => {});
  }, []);

  async function saveAccount(e) {
    e.preventDefault();
    setAccountBusy(true); setAccountMsg(null);
    try {
      const updated = await updateAccount(accountForm);
      setAccount(updated);
      setAccountMsg({ kind: "ok", text: "Ma'lumotlar saqlandi." });
    } catch (err) {
      setAccountMsg({ kind: "bad", text: err.data?.email?.[0] || err.message || "Saqlab bo'lmadi." });
    }
    setAccountBusy(false);
  }

  async function savePassword(e) {
    e.preventDefault();
    setPwMsg(null);
    if (pwForm.new_password !== pwForm.confirm) {
      setPwMsg({ kind: "bad", text: "Yangi parollar mos kelmadi." });
      return;
    }
    if (pwForm.new_password.length < 8) {
      setPwMsg({ kind: "bad", text: "Yangi parol kamida 8 belgidan iborat bo'lsin." });
      return;
    }
    setPwBusy(true);
    try {
      await changePassword(pwForm.old_password, pwForm.new_password);
      setPwForm({ old_password: "", new_password: "", confirm: "" });
      setPwMsg({ kind: "ok", text: "Parol muvaffaqiyatli yangilandi." });
    } catch (err) {
      setPwMsg({ kind: "bad", text: err.data?.old_password?.[0] || err.message || "Parolni yangilab bo'lmadi." });
    }
    setPwBusy(false);
  }

  async function pickAvatar(avatarId) {
    setAvatarBusy(true);
    try {
      const updated = await updateProfile({ avatar_preference: avatarId });
      setMe(updated);
    } catch { /* e'tiborsiz — avatar tanlash ixtiyoriy */ }
    setAvatarBusy(false);
  }

  const currentAvatarId = me?.avatar_preference?.id ?? me?.avatar_preference;
  const p = dashboard;
  const initials = (account?.first_name || account?.email || "?").trim().charAt(0).toUpperCase();

  return (
    <div className="ui prof">
      <header className="ui-head">
        <div>
          <h1>{t("nav.profile")}</h1>
          <p>Shaxsiy ma'lumotlar, xavfsizlik, statistika va obuna — barchasi bitta joyda.</p>
        </div>
      </header>

      <div className="prof-grid">
        {/* Avatar + hisob ma'lumotlari */}
        <section className="ui-card prof-card">
          <h2>Shaxsiy ma'lumotlar</h2>
          <div className="prof-avatar-row">
            <div className="prof-avatar-big">
              {avatars?.find(a => a.id === currentAvatarId)?.preview_image_url
                ? <img src={avatars.find(a => a.id === currentAvatarId).preview_image_url} alt="" />
                : <span>{initials}</span>}
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: 16 }}>{account?.first_name || account?.username || "..."}</div>
              <div className="ui-faint">{account?.email}</div>
            </div>
          </div>

          {avatars?.length > 0 && (
            <>
              <div className="prof-subhead">Profil rasmi uchun avatar tanlang</div>
              <div className="prof-avatar-grid">
                {avatars.slice(0, 8).map(a => (
                  <button key={a.id} type="button" className={"prof-avatar-pick" + (a.id === currentAvatarId ? " on" : "")}
                    disabled={avatarBusy} onClick={() => pickAvatar(a.id)} title={a.name}>
                    {a.preview_image_url ? <img src={a.preview_image_url} alt={a.name} /> : <span>{a.name?.[0]}</span>}
                  </button>
                ))}
              </div>
            </>
          )}

          <form onSubmit={saveAccount} className="prof-form">
            <div className="prof-field-row">
              <label className="field">
                <span>Ism</span>
                <input className="input" value={accountForm.first_name}
                  onChange={e => setAccountForm(f => ({ ...f, first_name: e.target.value }))} />
              </label>
              <label className="field">
                <span>Familiya</span>
                <input className="input" value={accountForm.last_name}
                  onChange={e => setAccountForm(f => ({ ...f, last_name: e.target.value }))} />
              </label>
            </div>
            <label className="field">
              <span>Email</span>
              <input className="input" type="email" value={accountForm.email}
                onChange={e => setAccountForm(f => ({ ...f, email: e.target.value }))} />
            </label>
            {accountMsg && <div className={"ui-alert" + (accountMsg.kind === "bad" ? " bad" : "")}>{accountMsg.text}</div>}
            <button type="submit" className="ui-btn primary" disabled={accountBusy}>
              {accountBusy ? "Saqlanmoqda..." : "Saqlash"}
            </button>
          </form>
        </section>

        {/* Parol o'zgartirish */}
        <section className="ui-card prof-card">
          <h2>Parolni almashtirish</h2>
          <form onSubmit={savePassword} className="prof-form">
            <label className="field">
              <span>Joriy parol</span>
              <input className="input" type="password" value={pwForm.old_password}
                onChange={e => setPwForm(f => ({ ...f, old_password: e.target.value }))} autoComplete="current-password" />
            </label>
            <label className="field">
              <span>Yangi parol</span>
              <input className="input" type="password" value={pwForm.new_password}
                onChange={e => setPwForm(f => ({ ...f, new_password: e.target.value }))} autoComplete="new-password" placeholder="kamida 8 belgi" />
            </label>
            <label className="field">
              <span>Yangi parolni tasdiqlang</span>
              <input className="input" type="password" value={pwForm.confirm}
                onChange={e => setPwForm(f => ({ ...f, confirm: e.target.value }))} autoComplete="new-password" />
            </label>
            {pwMsg && <div className={"ui-alert" + (pwMsg.kind === "bad" ? " bad" : "")}>{pwMsg.text}</div>}
            <button type="submit" className="ui-btn primary" disabled={pwBusy}>
              {pwBusy ? "Yangilanmoqda..." : "Parolni yangilash"}
            </button>
          </form>
        </section>

        {/* Statistika */}
        <section className="ui-card prof-card">
          <h2>Mening statistikam</h2>
          {!p && <div className="ui-skeleton" style={{ height: 120 }} />}
          {p && (
            <div className="prof-stats-grid">
              <div className="prof-stat"><div className="prof-stat-n">{p.streak ?? 0}</div><div className="ui-faint">kunlik seriya</div></div>
              <div className="prof-stat"><div className="prof-stat-n">{p.points?.total ?? 0}</div><div className="ui-faint">jami ball</div></div>
              <div className="prof-stat"><div className="prof-stat-n">{p.total_minutes ?? 0}</div><div className="ui-faint">daqiqa (jami)</div></div>
              <div className="prof-stat"><div className="prof-stat-n">{p.learning?.ai_lessons ?? 0}</div><div className="ui-faint">tugatilgan dars</div></div>
            </div>
          )}
          {p?.levels?.length > 0 && (
            <>
              <div className="prof-subhead">Darajalarim</div>
              <div className="ui-chips">
                {p.levels.map(l => <span key={l.subject_code} className="ui-chip">{l.subject_name}: {l.level}</span>)}
              </div>
            </>
          )}
        </section>

        {/* Obuna */}
        <section className="ui-card prof-card">
          <h2>Obuna</h2>
          {!status && <div className="ui-skeleton" style={{ height: 60 }} />}
          {status && (
            <div className="prof-sub-row">
              <div>
                <div style={{ fontWeight: 700 }}>{status.active ? (status.plan || "Premium") : "Bepul tarif"}</div>
                <p className="ui-faint" style={{ margin: "4px 0 0" }}>
                  {status.active
                    ? (status.expires_at ? `${new Date(status.expires_at).toLocaleDateString("ru-RU")} gacha amal qiladi` : "Muddatsiz")
                    : "Premium'ga o'tib qo'shimcha imkoniyatlarni oching."}
                </p>
              </div>
              <Link to="/app/billing" className="ui-btn">Boshqarish</Link>
            </div>
          )}
        </section>

        {/* Sozlamalar */}
        <section className="ui-card prof-card">
          <h2>Sozlamalar</h2>
          <div className="prof-subhead">Interfeys tili</div>
          <div className="ui-chips">
            {languages.map(l => (
              <button key={l.code} type="button" className={"ui-chip" + (l.code === lang ? " on" : "")}
                onClick={() => setLang(l.code)}>
                {l.flag} {l.label}
              </button>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
