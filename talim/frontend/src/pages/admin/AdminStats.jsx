import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchAdminOverview } from "../../api/client.js";
import { AdminPageHeader, DemoBanner } from "./AdminLayout.jsx";

const uzs = n => `${Math.round(n).toLocaleString("ru-RU").replace(/,/g, " ")} so'm`;

export default function AdminStats() {
  const [d, setD] = useState(null);
  const [isDemo, setIsDemo] = useState(false);
  useEffect(() => { fetchAdminOverview().then(setD).catch(err => { if (err.isNetworkError) setIsDemo(true); }); }, []);

  const cards = d ? [
    { label: "Foydalanuvchilar", value: d.total_users, hint: `+${d.new_users_week ?? 0} shu hafta` },
    { label: "Premium", value: d.premium_users, hint: d.total_users ? `${Math.round((d.premium_users / d.total_users) * 100)}% foydalanuvchilar` : "" },
    { label: "Bugun faol", value: d.active_today ?? "—", hint: `7 kunda: ${d.active_week ?? "—"}` },
    { label: "Shu oy tushum", value: d.revenue_month_uzs != null ? uzs(d.revenue_month_uzs) : "—", hint: "Payme + Click (demo to'lovlarsiz)" },
    { label: "AI Ustozga savollar", value: d.ai_messages_today ?? "—", hint: "bugun" },
    { label: "Avatar suhbatlari", value: d.today_sessions, hint: "bugun boshlangan" },
    { label: "Ochiq murojaatlar", value: d.open_tickets ?? 0, hint: <Link to="/app/admin/tickets">Ko'rish</Link>, warn: d.open_tickets > 0 },
    { label: "O'rtacha streak", value: `${d.avg_streak_days} kun`, hint: "fanlar bo'yicha" },
  ] : [];
  const maxMin = Math.max(10, ...(d?.week || []).map(w => w.minutes));

  return (
    <div>
      <AdminPageHeader title="Statistika" subtitle="Butun platforma bo'yicha asosiy ko'rsatkichlar" />
      <DemoBanner show={isDemo} />
      <div className="adm-stat-grid">
        {cards.map(c => (
          <div key={c.label} className={"adm-stat" + (c.warn ? " warn" : "")}>
            <span>{c.label}</span><strong>{c.value}</strong><small>{c.hint}</small>
          </div>
        ))}
      </div>
      {d?.week && (
        <div className="adm-chart">
          <h3>Oxirgi 7 kun: o'qishga sarflangan vaqt (daqiqa) va yangi foydalanuvchilar</h3>
          <div className="adm-bars">
            {d.week.map(w => (
              <div key={w.date} className="adm-bar" title={`${w.minutes} daq · ${w.signups} yangi`}>
                <b>{w.minutes}</b>
                <i style={{ height: `${(w.minutes / maxMin) * 100}%` }} />
                <span>{w.label}{w.signups ? ` · +${w.signups}` : ""}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
