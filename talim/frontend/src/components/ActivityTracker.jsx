import { useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import { logActivity } from "../api/client.js";

const TRACKED_ROUTES = [
  "/app/chat",
  "/app/math",
  "/app/practice",
  "/app/quiz",
  "/app/word-game",
  "/app/videos",
  "/app/courses",
  "/app/ai-chat",
  "/app/vocabulary",
];

function getSubjectFromPath(pathname) {
  if (pathname.startsWith("/app/math")) return "math";
  return "english";
}

export default function ActivityTracker() {
  const location = useLocation();

  const startTimeRef = useRef(Date.now());
  const sentMinutesRef = useRef(0);

  const isTracked = TRACKED_ROUTES.some((route) =>
    location.pathname.startsWith(route)
  );

  useEffect(() => {
    if (!isTracked) {
      startTimeRef.current = Date.now();
      sentMinutesRef.current = 0;
      return;
    }

    startTimeRef.current = Date.now();
    sentMinutesRef.current = 0;

    const sendActivity = async () => {
      const elapsedMs = Date.now() - startTimeRef.current;
      const totalMinutes = Math.floor(elapsedMs / 60000);

      const unsentMinutes = totalMinutes - sentMinutesRef.current;

      if (unsentMinutes <= 0) return;

      const subject = getSubjectFromPath(location.pathname);

      try {
        await logActivity(subject, unsentMinutes, 0);
        sentMinutesRef.current += unsentMinutes;
      } catch (error) {
        console.error("Activity yuborilmadi:", error);
      }
    };

    // Har 1 daqiqada yig'ilgan vaqtni backendga yuboradi
    const interval = setInterval(sendActivity, 60000);

    // Sahifadan chiqishda qolgan vaqtni yuborishga harakat qiladi
    const handleBeforeUnload = () => {
      const elapsedMs = Date.now() - startTimeRef.current;
      const totalMinutes = Math.floor(elapsedMs / 60000);
      const unsentMinutes = totalMinutes - sentMinutesRef.current;

      if (unsentMinutes <= 0) return;

      const token = localStorage.getItem("st_access_token");
      if (!token) return;

      const subject = getSubjectFromPath(location.pathname);

      fetch(
        `${import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1"}/statistics/log-activity/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            subject_code: subject,
            minutes: unsentMinutes,
            sessions: 0,
          }),
          keepalive: true,
        }
      ).catch(() => {});
    };

    window.addEventListener("beforeunload", handleBeforeUnload);

    return () => {
      clearInterval(interval);
      window.removeEventListener("beforeunload", handleBeforeUnload);

      // React Router orqali boshqa sahifaga o'tganda
      sendActivity();
    };
  }, [location.pathname, isTracked]);

  return null;
}