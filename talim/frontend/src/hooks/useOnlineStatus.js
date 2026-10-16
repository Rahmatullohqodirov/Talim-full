import { useEffect, useState } from "react";
import { pingBackend } from "../api/client.js";

/**
 * Ilova ikkita holatni kuzatadi:
 *  - browserOnline: qurilma umuman internetga ulanganmi (navigator.onLine)
 *  - backendReachable: bizning Django serverimiz javob berayaptimi
 *
 * Ikkalasi ham true bo'lsagina "online" deb hisoblanadi — aks holda ilova
 * avtomatik demo (mock) ma'lumotlarga o'tadi, lekin ishlashda davom etadi.
 */
export function useOnlineStatus(pollMs = 15000) {
  const [browserOnline, setBrowserOnline] = useState(navigator.onLine);
  const [backendReachable, setBackendReachable] = useState(true);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    function onOnline() { setBrowserOnline(true); }
    function onOffline() { setBrowserOnline(false); setBackendReachable(false); setChecking(false); }
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    return () => {
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function check() {
      if (!navigator.onLine) {
        if (!cancelled) { setBackendReachable(false); setChecking(false); }
        return;
      }
      const ok = await pingBackend();
      if (!cancelled) { setBackendReachable(ok); setChecking(false); }
    }
    check();
    const id = setInterval(check, pollMs);
    return () => { cancelled = true; clearInterval(id); };
  }, [pollMs]);

  return {
    isOnline: browserOnline && backendReachable,
    browserOnline,
    backendReachable,
    checking,
  };
}
