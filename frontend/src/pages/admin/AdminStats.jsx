import React, { useEffect, useState } from "react";
import { adminStatCards as mockCards } from "../../data/mockData.js";
import { fetchAdminOverview } from "../../api/client.js";
import { AdminPageHeader, DemoBanner } from "./AdminLayout.jsx";

export default function AdminStats() {
  const [cards, setCards] = useState(mockCards);
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    fetchAdminOverview()
      .then(data => {
        setIsDemo(false);
        if (data) {
          setCards([
            { label: "Jami foydalanuvchilar", value: String(data.total_users) },
            { label: "Faol premium", value: String(data.premium_users) },
            { label: "Bugungi sessiyalar", value: String(data.today_sessions) },
            { label: "O'rtacha streak", value: `${data.avg_streak_days} kun` },
          ]);
        }
      })
      .catch(err => { if (err.isNetworkError) setIsDemo(true); });
  }, []);

  return (
    <div>
      <AdminPageHeader title="Umumiy statistika" subtitle="Butun platforma bo'yicha ko'rsatkichlar" />
      <DemoBanner show={isDemo} />
      <div className="grid-4">
        {cards.map((c, i) => (
          <div key={i} className="subject-tile">
            <div style={{ fontSize: 12.5, color: "var(--text-muted)", fontWeight: 600, marginBottom: 8 }}>{c.label}</div>
            <div style={{ fontFamily: "var(--font-display)", fontSize: 27, fontWeight: 800 }}>{c.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
