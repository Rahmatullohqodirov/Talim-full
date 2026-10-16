import React, { useEffect, useState } from "react";
import { adminPayments as mockPayments } from "../../data/mockData.js";
import { fetchAdminPayments, updateAdminPayment, deleteAdminPayment } from "../../api/client.js";
import { AdminPageHeader, RowActions, DemoBanner } from "./AdminLayout.jsx";

const statusLabel = { success: "To'landi", pending: "Kutilmoqda", failed: "Muvaffaqiyatsiz", cancelled: "Bekor qilindi" };
const statusChoices = ["pending", "success", "failed", "cancelled"];

export default function AdminPayments() {
  const [payments, setPayments] = useState(mockPayments.map(p => ({ ...p, id: null })));
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    fetchAdminPayments()
      .then(data => {
        setIsDemo(false);
        setPayments((data || []).map(p => ({
          id: p.id, user: p.username, plan: p.plan_name, provider: p.provider,
          amount: Number(p.amount_uzs).toLocaleString() + " so'm", status: p.status,
          date: (p.paid_at || p.created_at || "").slice(0, 10),
        })));
      })
      .catch(err => { if (err.isNetworkError) setIsDemo(true); });
  }, []);

  async function handleStatusChange(p, newStatus) {
    const prev = p.status;
    setPayments(list => list.map(x => x.id === p.id ? { ...x, status: newStatus } : x));
    try {
      await updateAdminPayment(p.id, { status: newStatus });
    } catch {
      setPayments(list => list.map(x => x.id === p.id ? { ...x, status: prev } : x));
    }
  }

  return (
    <div>
      <AdminPageHeader title="To'lovlar" subtitle="Payme / Click orqali amalga oshirilgan tranzaksiyalar" />
      <DemoBanner show={isDemo} />
      <div className="admin-table">
        <div className="admin-table-head" style={{ gridTemplateColumns: "1.5fr 1.3fr 0.9fr 1fr 1fr 0.9fr 0.5fr" }}>
          <div>Foydalanuvchi</div><div>Reja</div><div>Provayder</div><div>Summa</div><div>Holat</div><div>Sana</div><div></div>
        </div>
        {payments.map((p, i) => (
          <div key={p.id ?? i} className="admin-table-row" style={{ gridTemplateColumns: "1.5fr 1.3fr 0.9fr 1fr 1fr 0.9fr 0.5fr" }}>
            <div style={{ fontWeight: 600 }}>{p.user}</div>
            <div>{p.plan}</div>
            <div>{p.provider}</div>
            <div>{p.amount}</div>
            <div>
              {p.id ? (
                <select
                  className="input" style={{ padding: "5px 8px", fontSize: 12.5, width: "auto" }}
                  value={p.status} onChange={e => handleStatusChange(p, e.target.value)}
                >
                  {statusChoices.map(s => <option key={s} value={s}>{statusLabel[s]}</option>)}
                </select>
              ) : (
                <span className={"badge " + (p.status === "success" ? "on" : "off")}>{statusLabel[p.status] || p.status}</span>
              )}
            </div>
            <div>{p.date}</div>
            <div>
              {p.id && p.status !== "success" && (
                <RowActions
                  onDelete={async () => {
                    await deleteAdminPayment(p.id);
                    setPayments(list => list.filter(x => x.id !== p.id));
                  }}
                  deleteLabel="Ushbu tranzaksiya yozuvini o'chirmoqchimisiz?"
                />
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
