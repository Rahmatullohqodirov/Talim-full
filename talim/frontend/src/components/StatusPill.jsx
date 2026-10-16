import React from "react";
import { useOnlineStatus } from "../hooks/useOnlineStatus.js";
import "./StatusPill.css";

export default function StatusPill() {
  const { isOnline, checking } = useOnlineStatus();
  const cls = checking ? "checking" : isOnline ? "online" : "offline";
  const text = checking ? "Tekshirilmoqda..." : isOnline ? "Onlayn" : "Offlayn (demo)";
  return (
    <span className={"status-pill " + cls}>
      <span className="dot" />
      {text}
    </span>
  );
}
