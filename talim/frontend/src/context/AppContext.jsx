import React, { createContext, useContext, useEffect, useState } from "react";
import { loginRequest, registerRequest, verifyEmailRequest, resendCodeRequest, socialLoginRequest, fetchMe } from "../api/client.js";

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem("st_access_token"));
  const [role, setRole] = useState(null); // 'student' | 'admin' — backenddagi is_staff'dan aniqlanadi
  const [meLoading, setMeLoading] = useState(isAuthenticated);

  useEffect(() => {
    if (!isAuthenticated) { setRole(null); setMeLoading(false); return; }
    setMeLoading(true);
    fetchMe()
      .then(profile => setRole(profile?.user?.is_staff ? "admin" : "student"))
      .catch(() => setRole("student"))
      .finally(() => setMeLoading(false));
  }, [isAuthenticated]);

  function applyTokens(data) {
    localStorage.setItem("st_access_token", data.access);
    localStorage.setItem("st_refresh_token", data.refresh);
    setIsAuthenticated(true);
  }

  async function login(username, password) {
    const data = await loginRequest(username, password); // throws on wrong credentials / unreachable API
    applyTokens(data);
    return data;
  }

  // Ro'yxatdan o'tgach ENDI avtomatik kirilmaydi — email tasdiqlanmaguncha hisob faol emas.
  // Chaqiruvchi (Register.jsx) natijada { needsVerification: true, email } oladi va
  // foydalanuvchini kod kiritish sahifasiga yo'naltiradi.
  async function register(payload) {
    await registerRequest(payload); // throws on validation errors / unreachable API
    return { needsVerification: true, email: payload.email };
  }

  async function verifyEmail(email, code) {
    const data = await verifyEmailRequest(email, code); // throws agar kod noto'g'ri/eskirgan bo'lsa
    applyTokens(data);
  }

  async function resendCode(email) {
    return resendCodeRequest(email);
  }

  async function socialLogin(provider, token) {
    const data = await socialLoginRequest(provider, token);
    applyTokens(data);
    return data; // {created, needs_onboarding}
  }

  function logout() {
    localStorage.removeItem("st_access_token");
    localStorage.removeItem("st_refresh_token");
    setIsAuthenticated(false);
    setRole(null);
  }

  return (
    <AppContext.Provider value={{ isAuthenticated, login, register, verifyEmail, resendCode, socialLogin, logout, role, meLoading }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}
