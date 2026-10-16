import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext.jsx";
import { fetchSocialConfig } from "../api/client.js";

/**
 * Google va Facebook orqali kirish.
 *
 * Kalitlar faqat backend .env faylida turadi (GOOGLE_CLIENT_ID, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET);
 * ochiq ID'lar /auth/social/config/ dan olinadi. Xohlasangiz frontend .env'dagi VITE_GOOGLE_CLIENT_ID /
 * VITE_FACEBOOK_APP_ID ular ustidan yoziladi. Hech biri sozlanmagan bo'lsa, tugmalar umuman ko'rinmaydi.
 */
const ENV_GOOGLE = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";
const ENV_FACEBOOK = import.meta.env.VITE_FACEBOOK_APP_ID || "";

let configPromise = null;
function loadConfig() {
  if (!configPromise) {
    configPromise = fetchSocialConfig()
      .then(c => ({ google: ENV_GOOGLE || c.google_client_id || "", facebook: ENV_FACEBOOK || c.facebook_app_id || "" }))
      .catch(() => ({ google: ENV_GOOGLE, facebook: ENV_FACEBOOK }));
  }
  return configPromise;
}

function loadScript(src, id) {
  return new Promise((resolve, reject) => {
    const existing = document.getElementById(id);
    if (existing) {
      if (existing.dataset.loaded) return resolve();
      existing.addEventListener("load", resolve);
      existing.addEventListener("error", reject);
      return;
    }
    const script = document.createElement("script");
    script.src = src;
    script.id = id;
    script.async = true;
    script.defer = true;
    script.onload = () => { script.dataset.loaded = "1"; resolve(); };
    script.onerror = reject;
    document.body.appendChild(script);
  });
}

export default function SocialLoginButtons({ onError, dividerLabel = "yoki" }) {
  const { socialLogin } = useApp();
  const navigate = useNavigate();
  const googleBoxRef = useRef(null);
  const [config, setConfig] = useState(null);
  const [fbReady, setFbReady] = useState(false);
  const [googleFailed, setGoogleFailed] = useState(false);
  const [busy, setBusy] = useState("");

  useEffect(() => { loadConfig().then(setConfig); }, []);

  async function finish(provider, token) {
    setBusy(provider);
    try {
      const data = await socialLogin(provider, token);
      navigate(data?.needs_onboarding ? "/onboarding" : "/app/dashboard", { replace: true });
    } catch (e) {
      onError?.(e.isNetworkError ? "Server bilan aloqa yo'q." : e.message || "Kirishda xatolik.");
    } finally {
      setBusy("");
    }
  }

  // Google Identity Services: rasmiy tugma (id_token beradi, backend uni Google'da tekshiradi)
  useEffect(() => {
    if (!config?.google) return;
    let cancelled = false;
    loadScript("https://accounts.google.com/gsi/client", "google-identity-script")
      .then(() => {
        if (cancelled || !window.google?.accounts?.id || !googleBoxRef.current) return;
        window.google.accounts.id.initialize({
          client_id: config.google,
          callback: resp => resp?.credential && finish("google", resp.credential),
          ux_mode: "popup",
          cancel_on_tap_outside: true,
        });
        const width = Math.min(400, Math.max(240, googleBoxRef.current.offsetWidth || 360));
        googleBoxRef.current.innerHTML = "";
        window.google.accounts.id.renderButton(googleBoxRef.current, {
          type: "standard", theme: "outline", size: "large", shape: "rectangular",
          text: "continue_with", logo_alignment: "center", width, locale: "uz",
        });
      })
      .catch(() => !cancelled && setGoogleFailed(true));
    return () => { cancelled = true; };
  }, [config?.google]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!config?.facebook) return;
    if (window.FB) { setFbReady(true); return; }
    window.fbAsyncInit = () => {
      window.FB.init({ appId: config.facebook, cookie: true, xfbml: false, version: "v19.0" });
      setFbReady(true);
    };
    loadScript("https://connect.facebook.net/en_US/sdk.js", "facebook-jssdk").catch(() => setFbReady(false));
  }, [config?.facebook]);

  function facebookLogin() {
    if (!window.FB) return;
    window.FB.login(resp => {
      if (resp.authResponse?.accessToken) finish("facebook", resp.authResponse.accessToken);
      else onError?.("Facebook orqali kirish bekor qilindi.");
    }, { scope: "email,public_profile" });
  }

  if (!config || (!config.google && !config.facebook)) return null;

  return (
    <div className="social">
      <div className="auth-divider">{dividerLabel}</div>
      <div className="social-btn-row">
        {config.google && (
          googleFailed ? (
            <p className="auth-hint">Google xizmatini yuklab bo'lmadi. Internetni tekshiring.</p>
          ) : (
            <div className={"social-google" + (busy === "google" ? " busy" : "")} ref={googleBoxRef} aria-label="Google orqali davom etish" />
          )
        )}
        {config.facebook && (
          <button type="button" className="social-btn" onClick={facebookLogin} disabled={!fbReady || !!busy}>
            <FacebookIcon /> {busy === "facebook" ? "Kirilmoqda..." : "Facebook orqali davom etish"}
          </button>
        )}
      </div>
    </div>
  );
}

function FacebookIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="#1877F2" aria-hidden="true">
      <path d="M22 12a10 10 0 10-11.56 9.88v-6.99H7.9V12h2.54V9.8c0-2.5 1.49-3.89 3.78-3.89 1.1 0 2.24.2 2.24.2v2.46h-1.26c-1.24 0-1.63.77-1.63 1.56V12h2.78l-.44 2.89h-2.34v6.99A10 10 0 0022 12z" />
    </svg>
  );
}
