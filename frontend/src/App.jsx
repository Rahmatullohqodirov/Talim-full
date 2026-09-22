import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useApp } from "./context/AppContext.jsx";
import Landing from "./pages/Landing.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import Onboarding from "./pages/Onboarding.jsx";
import AppLayout from "./pages/app/AppLayout.jsx";
import Dashboard from "./pages/app/Dashboard.jsx";
import Chat from "./pages/app/Chat.jsx";
import MathPractice from "./pages/app/MathPractice.jsx";
import Flashcards from "./pages/app/Flashcards.jsx";
import QuizPractice from "./pages/app/QuizPractice.jsx";
import Leaderboard from "./pages/app/Leaderboard.jsx";
import Videos from "./pages/app/Videos.jsx";
import Courses from "./pages/app/Courses.jsx";
import AIChat from "./pages/app/AIChat.jsx";
import Billing from "./pages/app/Billing.jsx";
import AdminLayout from "./pages/admin/AdminLayout.jsx";
import AdminUsers from "./pages/admin/AdminUsers.jsx";
import AdminSubjects from "./pages/admin/AdminSubjects.jsx";
import AdminAvatars from "./pages/admin/AdminAvatars.jsx";
import AdminProblems from "./pages/admin/AdminProblems.jsx";
import AdminStats from "./pages/admin/AdminStats.jsx";
import AdminVideos from "./pages/admin/AdminVideos.jsx";
import AdminPayments from "./pages/admin/AdminPayments.jsx";
import AdminFlashcards from "./pages/admin/AdminFlashcards.jsx";
import AdminLeaderboard from "./pages/admin/AdminLeaderboard.jsx";

function RequireAuth({ children }) {
  const { isAuthenticated } = useApp();
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

function RequireAdmin({ children }) {
  const { role, meLoading } = useApp();
  if (meLoading) return null;
  return role === "admin" ? children : <Navigate to="/app/dashboard" replace />;
}

function RequireStudent({ children }) {
  const { role, meLoading } = useApp();
  if (meLoading) return null;
  return role === "admin" ? <Navigate to="/app/admin" replace /> : children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/onboarding" element={<RequireAuth><Onboarding /></RequireAuth>} />

      <Route path="/app" element={<RequireAuth><AppLayout /></RequireAuth>}>
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<RequireStudent><Dashboard /></RequireStudent>} />
        <Route path="chat" element={<RequireStudent><Chat /></RequireStudent>} />
        <Route path="math" element={<RequireStudent><MathPractice /></RequireStudent>} />
        <Route path="practice" element={<RequireStudent><Flashcards /></RequireStudent>} />
        <Route path="quiz" element={<RequireStudent><QuizPractice /></RequireStudent>} />
        <Route path="leaderboard" element={<RequireStudent><Leaderboard /></RequireStudent>} />
        <Route path="videos" element={<RequireStudent><Videos /></RequireStudent>} />
        <Route path="courses" element={<RequireStudent><Courses /></RequireStudent>} />
        <Route path="ai-chat" element={<RequireStudent><AIChat /></RequireStudent>} />
        <Route path="billing" element={<RequireStudent><Billing /></RequireStudent>} />
        <Route path="admin" element={<RequireAdmin><AdminLayout /></RequireAdmin>}>
          <Route index element={<Navigate to="users" replace />} />
          <Route path="users" element={<AdminUsers />} />
          <Route path="subjects" element={<AdminSubjects />} />
          <Route path="avatars" element={<AdminAvatars />} />
          <Route path="problems" element={<AdminProblems />} />
          <Route path="flashcards" element={<AdminFlashcards />} />
          <Route path="leaderboard" element={<AdminLeaderboard />} />
          <Route path="videos" element={<AdminVideos />} />
          <Route path="payments" element={<AdminPayments />} />
          <Route path="stats" element={<AdminStats />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
