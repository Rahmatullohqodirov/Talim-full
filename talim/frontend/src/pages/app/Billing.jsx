import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { createPayment, fetchSubscriptionStatus, fetchTransactions } from "../../api/client.js";
import "./ui.css";
import "./Billing.css";

const STATUS = {
  success: ["To'landi", "ok"], pending: ["Kutilmoqda", "pen"], failed: ["Muvaffaqiyatsiz", "bad"], cancelled: ["Bekor qilindi", ""],
};
const FREE_FEATURES = ["AI Ustoz bilan suhbat", "So'zlar, quiz va matematika", "Kunlik / haftalik reja", "Reyting va statistika"];
const fmtUzs = n => `${Number(n).toLocaleString("ru-RU").replace(/,/g, " ")} so'm`;
const fmtDate = iso => (iso ? new Date(iso).toLocaleDateString("ru-RU") : "");

export default function Billing() {
  const [status, setStatus] = useState(null);
  const [history, setHistory] = useState(null);
  const [provider, setProvider] = useState("payme");
  const [busy, setBusy] = useState(null);
  const [notice, setNotice] = useState(null); // {kind, text}
  const [params, setParams] = useSearchParams();

  function load() {
    fetchSubscriptionStatus().then(s => {
      setStatus(s);
      if (!s.providers.payme && s.providers.click) setProvider("click");
    }).catch(e => setNotice({ kind: "bad", text: e.isNetworkError ? "Server bilan aloqa yo'q." : e.message }));
    fetchTransactions().then(d => setHistory(Array.isArray(d) ? d : d?.results || [])).catch(() => setHistory([]));
  }
  useEffect(load, []);

  // Payme/Click'dan qaytilganda: to'lov holatini bir necha marta tekshiramiz
  useEffect(() => {
    const paid = params.get("paid");
    if (!paid) return;
    setNotice({ kind: "", text: "To'lov tekshirilmoqda..." });
    let tries = 0;
    const t = setInterval(async () => {
      tries += 1;
      try {
        const list = await fetchTransactions();
        const txn = (Array.isArray(list) ? list : list?.results || []).find(x => x.id === paid);
        if (txn?.status === "success") {
          clearInterval(t); setNotice({ kind: "ok", text: "To'lov qabul qilindi. Premium faollashtirildi!" }); setParams({}, { replace: true }); load();
        } else if (txn && ["failed", "cancelled"].includes(txn.status)) {
          clearInterval(t); setNotice({ kind: "bad", text: "To'lov amalga oshmadi. Qayta urinib ko'ring." }); setParams({}, { replace: true }); load();
        }
      } catch { /* keyingi urinish */ }
      if (tries >= 10) { clearInterval(t); setNotice({ kind: "", text: "To'lov hali tasdiqlanmadi. Bir necha daqiqadan keyin sahifani yangilang." }); }
    }, 3000);
    return () => clearInterval(t);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function buy(plan) {
    setBusy(plan.id); setNotice(null);
    try {
      const res = await createPayment(plan.id, provider);
      if (res.mock) {
        setNotice({ kind: "ok", text: "Demo rejim: to'lov sinov sifatida qabul qilindi va Premium yoqildi. Haqiqiy to'lov uchun serverda Payme/Click kalitlarini sozlang." });
        load();
      } else if (res.checkout_url) {
        window.location.href = res.checkout_url;
        return;
      }
    } catch (e) {
      setNotice({ kind: "bad", text: e.message || "To'lovni boshlab bo'lmadi." });
    }
    setBusy(null);
  }

  const plans = status?.plans || [];

  return (
    <div className="ui bill">
      <header className="ui-head">
        <div>
          <h1>Obuna</h1>
          <p>Premium bilan barcha avatarlar va qo'shimcha imkoniyatlar ochiladi. To'lov Payme yoki Click orqali, so'mda.</p>
        </div>
      </header>

      {notice && <div className={"ui-alert " + (notice.kind === "bad" ? "bad" : "")} role="status" style={notice.kind === "ok" ? { background: "var(--u-ok-wash)", color: "oklch(0.38 0.1 155)" } : undefined}>{notice.text}</div>}

      {!status && !notice && <div className="ui-skeleton" style={{ height: 120 }} />}

      {status && (
        <section className={"ui-card bill-current" + (status.active ? " premium" : "")}>
          <div>
            <span className="bill-current-label">Joriy tarif</span>
            <h2>{status.active ? (status.plan || "Premium") : "Bepul"}</h2>
            <p className="ui-muted">
              {status.active
                ? (status.expires_at ? <>Amal qiladi: <strong>{fmtDate(status.expires_at)}</strong> gacha · {status.days_left} kun qoldi</> : "Muddatsiz")
                : "Asosiy bo'limlar bepul. Premium'ga o'tib qo'shimcha imkoniyatlarni oching."}
            </p>
          </div>
          {status.active && status.days_left !== null && status.days_left <= 5 && <span className="ui-badge pen">Tez orada tugaydi</span>}
        </section>
      )}

      {status && (
        <section className="bill-plans">
          <div className="ui-card bill-plan">
            <h3>Bepul</h3>
            <div className="bill-price">0 <small>so'm</small></div>
            <ul>{FREE_FEATURES.map(f => <li key={f}>{f}</li>)}</ul>
            <button className="ui-btn" disabled>{status.active ? "Asosiy tarif" : "Joriy tarif"}</button>
          </div>
          {plans.map(p => (
            <div key={p.id} className="ui-card bill-plan featured">
              <span className="bill-tag">Tavsiya</span>
              <h3>{p.name}</h3>
              <div className="bill-price">{Number(p.price_uzs).toLocaleString("ru-RU").replace(/,/g, " ")} <small>so'm / {p.duration_days} kun</small></div>
              <p className="ui-faint bill-usd">≈ ${p.price_usd}</p>
              <ul>
                <li>Bepul tarifdagi hammasi</li>
                {p.features.map(f => <li key={f}>{f}</li>)}
              </ul>
              <div className="bill-providers" role="radiogroup" aria-label="To'lov usuli">
                {["payme", "click"].map(pr => (
                  <button key={pr} role="radio" aria-checked={provider === pr} disabled={!status.providers[pr]}
                    className={"bill-provider " + pr + (provider === pr ? " on" : "")} onClick={() => setProvider(pr)}
                    title={!status.providers[pr] ? "Hozircha ishlamayapti" : undefined}>
                    {pr === "payme" ? "Payme" : "Click"}
                  </button>
                ))}
              </div>
              <button className="ui-btn primary bill-buy" onClick={() => buy(p)} disabled={busy === p.id || !status.providers[provider]}>
                {busy === p.id ? "Yo'naltirilmoqda..." : status.active ? "Muddatni uzaytirish" : "Premium'ga o'tish"}
              </button>
              {status.demo_mode && <p className="ui-faint bill-demo">Sinov rejimi: haqiqiy pul yechilmaydi.</p>}
            </div>
          ))}
        </section>
      )}

      <section className="ui-card">
        <h2 style={{ marginBottom: 12 }}>To'lovlar tarixi</h2>
        {history === null && <div className="ui-skeleton" style={{ height: 60 }} />}
        {history?.length === 0 && <p className="ui-muted">Hali to'lov qilinmagan.</p>}
        {history?.length > 0 && (
          <ul className="bill-history">
            {history.map(t => (
              <li key={t.id}>
                <span className="bill-h-plan">{t.plan_name}</span>
                <span className="ui-faint">{t.provider === "payme" ? "Payme" : "Click"} · {fmtDate(t.created_at)}</span>
                <span className="bill-h-amount">{fmtUzs(t.amount_uzs)}</span>
                <span className={"ui-badge " + (STATUS[t.status]?.[1] || "")}>{STATUS[t.status]?.[0] || t.status}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
