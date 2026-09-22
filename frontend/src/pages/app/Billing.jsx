import React, { useEffect, useState } from "react";
import { paymentPlans, transactionHistory } from "../../data/mockData.js";
import { createPayment, fetchPlans, fetchTransactions } from "../../api/client.js";
import "./Billing.css";

const STATUS_LABELS = {
  success: "To'landi",
  pending: "Kutilmoqda",
  failed: "Muvaffaqiyatsiz",
  cancelled: "Bekor qilindi",
};

export default function Billing() {
  const [history, setHistory] = useState(transactionHistory);
  const [usingRealHistory, setUsingRealHistory] = useState(false);
  const [pending, setPending] = useState(null);
  const [plans, setPlans] = useState(paymentPlans);
  const [usingApi, setUsingApi] = useState(false);
  // Har bir reja uchun tanlangan to'lov provayderi alohida saqlanadi
  const [providerByPlan, setProviderByPlan] = useState({});

  function loadHistory() {
    fetchTransactions()
      .then(data => {
        const rows = Array.isArray(data) ? data : (data?.results || []);
        setHistory(rows.map(t => ({
          plan: t.plan_name || t.plan?.name || t.plan,
          provider: t.provider === "payme" ? "Payme" : "Click",
          amount: `${Number(t.amount_uzs).toLocaleString("uz-UZ")} so'm`,
          status: t.status,
          date: t.created_at ? new Date(t.created_at).toLocaleDateString("uz-UZ") : "",
        })));
        setUsingRealHistory(true);
      })
      .catch(() => setUsingRealHistory(false));
  }

  useEffect(() => {
    fetchPlans()
      .then(data => {
        if (data && data.length) {
          setPlans(data.map(p => ({
            id: p.id, name: p.name,
            price: Number(p.price_usd) === 0 ? "Bepul" : `$${p.price_usd}/oy`,
          })));
          setUsingApi(true);
        }
      })
      .catch(() => {});
    loadHistory();
  }, []);

  function selectProvider(planId, provider) {
    setProviderByPlan(m => ({ ...m, [planId]: provider }));
  }

  async function handleBuy(plan) {
    const provider = providerByPlan[plan.id] || "payme";
    if (!usingApi) {
      alert("Demo rejim: backend ulanmagan, to'lov havolasi generatsiya qilinmadi.");
      return;
    }
    setPending(plan.id);
    try {
      const res = await createPayment(plan.id, provider);
      if (res.mock) {
        alert("To'lov (demo rejim) muvaffaqiyatli amalga oshirildi! Haqiqiy to'lovlar uchun .env fayliga PAYME_MERCHANT_ID / CLICK_MERCHANT_ID qo'shing.");
        loadHistory();
      } else if (res.checkout_url) {
        window.location.href = res.checkout_url;
      }
    } catch (e) {
      alert("Xato: " + e.message);
    }
    setPending(null);
  }

  return (
    <div>
      <h1 className="page-title">Obuna va to'lovlar</h1>
      <p className="page-sub">Premium rejaga o'ting — Payme yoki Click orqali to'lang</p>
      <div className="billing-grid">
        {plans.map(p => {
          const provider = providerByPlan[p.id] || "payme";
          return (
            <div key={p.id} className="plan-tile">
              <div className="plan-tile-name">{p.name}</div>
              <div className="plan-tile-price">{p.price}</div>
              <div className="provider-toggle">
                <button
                  type="button"
                  className={"provider-btn" + (provider === "payme" ? " active" : "")}
                  onClick={() => selectProvider(p.id, "payme")}
                >
                  Payme
                </button>
                <button
                  type="button"
                  className={"provider-btn" + (provider === "click" ? " active" : "")}
                  onClick={() => selectProvider(p.id, "click")}
                >
                  Click
                </button>
              </div>
              <button className="btn btn-primary" style={{ width: "100%" }} onClick={() => handleBuy(p)} disabled={pending === p.id}>
                {pending === p.id ? "Yuklanmoqda..." : `${provider === "payme" ? "Payme" : "Click"} orqali to'lash`}
              </button>
            </div>
          );
        })}
      </div>
      <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 12 }}>
        To'lovlar tarixi{!usingRealHistory && <span style={{ fontWeight: 500, color: "var(--text-muted)", fontSize: 12.5 }}> (demo ma'lumot — backend ulanmagan)</span>}
      </div>
      <div className="admin-table">
        <div className="admin-table-head" style={{ gridTemplateColumns: "1.6fr 1fr 1fr 1fr 1fr" }}>
          <div>Reja</div><div>Provayder</div><div>Summa</div><div>Holat</div><div>Sana</div>
        </div>
        {history.length === 0 && (
          <div className="admin-table-row" style={{ gridTemplateColumns: "1fr" }}>
            <div style={{ color: "var(--text-muted)" }}>Hozircha to'lovlar yo'q.</div>
          </div>
        )}
        {history.map((h, i) => (
          <div key={i} className="admin-table-row" style={{ gridTemplateColumns: "1.6fr 1fr 1fr 1fr 1fr" }}>
            <div style={{ fontWeight: 600 }}>{h.plan}</div>
            <div>{h.provider}</div>
            <div>{h.amount}</div>
            <div><span className={"badge " + (h.status === "success" ? "on" : "off")}>{STATUS_LABELS[h.status] || h.status}</span></div>
            <div>{h.date}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
