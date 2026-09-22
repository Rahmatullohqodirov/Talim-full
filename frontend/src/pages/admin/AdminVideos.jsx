import React, { useEffect, useState } from "react";
import { adminVideos as mockVideos } from "../../data/mockData.js";
import { fetchAdminVideos, createAdminVideo, updateAdminVideo, deleteAdminVideo } from "../../api/client.js";
import { AddModal, useModal, AdminPageHeader, RowActions, DemoBanner } from "./AdminLayout.jsx";

const diffOptions = [
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
];

export default function AdminVideos() {
  const { open, editItem, openModal, openEdit, closeModal } = useModal();
  const [videos, setVideos] = useState(mockVideos.map(v => ({ ...v, id: null })));
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    fetchAdminVideos()
      .then(data => {
        setIsDemo(false);
        setVideos((data || []).map(v => ({
          id: v.id, youtube_id: v.youtube_id, title: v.title, subject: v.subject_name || v.subject?.name || "—",
          difficulty: v.difficulty, rating: v.avg_rating, views: v.view_count,
        })));
      })
      .catch(err => { if (err.isNetworkError) setIsDemo(true); });
  }, []);

  return (
    <div>
      <AdminPageHeader
        title="Video kutubxonasi"
        subtitle="AI tomonidan tavsiya qilingan va keshlangan YouTube videolari"
        action={<button className="btn btn-primary" onClick={openModal}>+ Video qo'shish</button>}
      />
      <DemoBanner show={isDemo} />
      <div className="admin-table">
        <div className="admin-table-head" style={{ gridTemplateColumns: "2fr 1fr 1fr 0.8fr 1fr 0.5fr" }}>
          <div>Video</div><div>Fan</div><div>Daraja</div><div>Reyting</div><div>Ko'rishlar</div><div></div>
        </div>
        {videos.map((v, i) => (
          <div key={v.id ?? i} className="admin-table-row" style={{ gridTemplateColumns: "2fr 1fr 1fr 0.8fr 1fr 0.5fr" }}>
            <div style={{ fontWeight: 600 }}>{v.title}</div>
            <div>{v.subject}</div>
            <div>{v.difficulty}</div>
            <div>⭐ {v.rating}</div>
            <div>{(v.views || 0).toLocaleString()}</div>
            <div>
              {v.id && (
                <RowActions
                  onEdit={() => openEdit(v)}
                  onDelete={async () => {
                    await deleteAdminVideo(v.id);
                    setVideos(list => list.filter(x => x.id !== v.id));
                  }}
                  deleteLabel={`"${v.title}" videosini o'chirmoqchimisiz?`}
                />
              )}
            </div>
          </div>
        ))}
      </div>

      {open && !editItem && (
        <AddModal
          title="Video qo'shish"
          fields={[
            { name: "youtube_id", label: "YouTube ID (masalan: dQw4w9WgXcQ)" },
            { name: "title", label: "Sarlavha" },
            { name: "channel_title", label: "Kanal nomi" },
            { name: "language", label: "Til kodi (masalan: en, uz)" },
            { name: "difficulty", label: "Daraja", type: "select", options: diffOptions },
          ]}
          onSubmit={async (v) => {
            const created = await createAdminVideo(v);
            setVideos(list => [{ id: created.id, youtube_id: created.youtube_id, title: created.title, subject: "—", difficulty: created.difficulty, rating: created.avg_rating, views: created.view_count }, ...list]);
          }}
          onClose={closeModal}
        />
      )}
      {open && editItem && (
        <AddModal
          title={`${editItem.title} — tahrirlash`}
          initialValues={{ title: editItem.title, difficulty: editItem.difficulty }}
          fields={[
            { name: "title", label: "Sarlavha" },
            { name: "difficulty", label: "Daraja", type: "select", options: diffOptions },
          ]}
          onSubmit={async (v) => {
            const updated = await updateAdminVideo(editItem.id, v);
            setVideos(list => list.map(x => x.id === editItem.id ? { ...x, title: updated.title, difficulty: updated.difficulty } : x));
          }}
          onClose={closeModal}
        />
      )}
    </div>
  );
}
