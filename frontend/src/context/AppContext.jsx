import React, { createContext, useContext, useEffect, useState } from "react";
import { loginRequest, registerRequest, fetchMe } from "../api/client.js";

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

  async function login(username, password) {
    const data = await loginRequest(username, password); // throws on wrong credentials / unreachable API
    localStorage.setItem("st_access_token", data.access);
    localStorage.setItem("st_refresh_token", data.refresh);
    setIsAuthenticated(true);
  }

  async function register(payload) {
    await registerRequest(payload); // throws on validation errors / unreachable API
    return login(payload.username, payload.password);
  }

  function logout() {
    localStorage.removeItem("st_access_token");
    localStorage.removeItem("st_refresh_token");
    setIsAuthenticated(false);
    setRole(null);
  }

  return (
    <AppContext.Provider value={{ isAuthenticated, login, register, logout, role, meLoading }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}
