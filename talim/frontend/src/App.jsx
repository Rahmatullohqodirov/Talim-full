import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useApp } from "./context/AppContext.jsx";
import VocabularyLevel from "./pages/VocabularyLevel.jsx";
import ActivityTracker from "./components/ActivityTracker.jsx";
import LanguageSwitcher from "./components/LanguageSwitcher.jsx";
import Words from "./pages/Words.jsx";
import Dictionary from "./pages/Dictionary.jsx";
import Landing from "./pages/Landing.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import VerifyEmail from "./pages/VerifyEmail.jsx";
import Onboarding from "./pages/Onboarding.jsx";

import AppLayout from "./pages/app/AppLayout.jsx";
import Dashboard from "./pages/app/Dashboard.jsx";
import Chat from "./pages/app/Chat.jsx";
import MathPractice from "./pages/app/MathPractice.jsx";
import QuizPractice from "./pages/app/QuizPractice.jsx";
import Leaderboard from "./pages/app/Leaderboard.jsx";
import Videos from "./pages/app/Videos.jsx";
import Courses from "./pages/app/Courses.jsx";
import AIChat from "./pages/app/AIChat.jsx";
import Billing from "./pages/app/Billing.jsx";
import Lessons from "./pages/app/Lessons.jsx";
import LessonDetail from "./pages/app/LessonDetail.jsx";
import StoryReader from "./pages/app/StoryReader.jsx";
import Profile from "./pages/app/Profile.jsx";

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
import AdminTickets from "./pages/admin/AdminTickets.jsx";
import AdminPlans from "./pages/admin/AdminPlans.jsx";
import AdminQuizzes from "./pages/admin/AdminQuizzes.jsx";
import AdminLessons from "./pages/admin/AdminLessons.jsx";
import AdminStories from "./pages/admin/AdminStories.jsx";

function RequireAuth({ children }) {
  const { isAuthenticated } = useApp();

  return isAuthenticated
    ? children
    : <Navigate to="/login" replace />;
}

function RequireAdmin({ children }) {
  const { role, meLoading } = useApp();

  if (meLoading) return null;

  return role === "admin"
    ? children
    : <Navigate to="/app/dashboard" replace />;
}

function RequireStudent({ children }) {
  const { role, meLoading } = useApp();

  if (meLoading) return null;

  return role === "admin"
    ? <Navigate to="/app/admin" replace />
    : children;
}

export default function App() {
  return (
    <>
      {/* Foydalanuvchi qancha vaqt mashq qilganini hisoblaydi */}
      <ActivityTracker />

      {/* Sayt burchagidagi til tanlagich — barcha sahifalarda ko'rinadi */}
      <LanguageSwitcher />

      <Routes>
        <Route path="/" element={<Landing />} />

        <Route path="/login" element={<Login />} />

        <Route path="/register" element={<Register />} />

        <Route
          path="/verify-email"
          element={<VerifyEmail />}
        />

        <Route
          path="/onboarding"
          element={
            <RequireAuth>
              <Onboarding />
            </RequireAuth>
          }
        />

        <Route
          path="/app"
          element={
            <RequireAuth>
              <AppLayout />
            </RequireAuth>
          }
        >
          <Route
            index
            element={<Navigate to="dashboard" replace />}
          />

          <Route
            path="dashboard"
            element={
              <RequireStudent>
                <Dashboard />
              </RequireStudent>
            }
          />

          <Route
            path="chat"
            element={
              <RequireStudent>
                <Chat />
              </RequireStudent>
            }
          />

          <Route
            path="math"
            element={
              <RequireStudent>
                <MathPractice />
              </RequireStudent>
            }
          />
          <Route path="practice" element={<Navigate to="/app/vocabulary?tab=cards" replace />} />

          {/* 📚 VOCABULARY */}
          <Route
            path="vocabulary"
            element={
              <RequireStudent>
                <Words />
              </RequireStudent>
            }
          />

          <Route
            path="dictionary"
            element={
              <RequireStudent>
                <Dictionary />
              </RequireStudent>
            }
          />

          <Route
            path="vocabulary/:level"
            element={
              <RequireStudent>
                <VocabularyLevel />
              </RequireStudent>
            }
          />

          <Route
            path="quiz"
            element={
              <RequireStudent>
                <QuizPractice />
              </RequireStudent>
            }
          />
          <Route path="word-game" element={<Navigate to="/app/vocabulary?tab=game" replace />} />

          <Route
            path="leaderboard"
            element={
              <RequireStudent>
                <Leaderboard />
              </RequireStudent>
            }
          />

          <Route
            path="videos"
            element={
              <RequireStudent>
                <Videos />
              </RequireStudent>
            }
          />

          <Route
            path="courses"
            element={
              <RequireStudent>
                <Courses />
              </RequireStudent>
            }
          />

          <Route
            path="ai-chat"
            element={
              <RequireStudent>
                <AIChat />
              </RequireStudent>
            }
          />

          <Route
            path="billing"
            element={
              <RequireStudent>
                <Billing />
              </RequireStudent>
            }
          />

          {/* 📖 DARSLAR va TINGLANG-O'QING */}
          <Route
            path="lessons"
            element={
              <RequireStudent>
                <Lessons />
              </RequireStudent>
            }
          />
          <Route
            path="lessons/:id"
            element={
              <RequireStudent>
                <LessonDetail />
              </RequireStudent>
            }
          />
          <Route
            path="stories/:id"
            element={
              <RequireStudent>
                <StoryReader />
              </RequireStudent>
            }
          />

          <Route
            path="profile"
            element={
              <RequireStudent>
                <Profile />
              </RequireStudent>
            }
          />

          <Route
            path="admin"
            element={
              <RequireAdmin>
                <AdminLayout />
              </RequireAdmin>
            }
          >
            <Route
              index
              element={<Navigate to="stats" replace />}
            />

            <Route
              path="users"
              element={<AdminUsers />}
            />

            <Route
              path="subjects"
              element={<AdminSubjects />}
            />

            <Route
              path="avatars"
              element={<AdminAvatars />}
            />

            <Route
              path="problems"
              element={<AdminProblems />}
            />

            <Route
              path="flashcards"
              element={<AdminFlashcards />}
            />

            <Route
              path="leaderboard"
              element={<AdminLeaderboard />}
            />

            <Route
              path="videos"
              element={<AdminVideos />}
            />

            <Route
              path="payments"
              element={<AdminPayments />}
            />

            <Route
              path="stats"
              element={<AdminStats />}
            />
            <Route path="tickets" element={<AdminTickets />} />
            <Route path="plans" element={<AdminPlans />} />
            <Route path="quizzes" element={<AdminQuizzes />} />
            <Route path="lessons" element={<AdminLessons />} />
            <Route path="stories" element={<AdminStories />} />
          </Route>
        </Route>

        <Route
          path="*"
          element={<Navigate to="/" replace />}
        />
      </Routes>
    </>
  );
}