const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

function authHeaders() {
  const token = localStorage.getItem("st_access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}
export const fetchYoutubeVideos = () => request("/youtube/videos/");

async function refreshAccessToken() {
  const refresh = localStorage.getItem("st_refresh_token");
  if (!refresh) return false;
  const res = await fetch(`${BASE_URL}/auth/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!res.ok) return false;
  const data = await res.json();
  localStorage.setItem("st_access_token", data.access);
  if (data.refresh) localStorage.setItem("st_refresh_token", data.refresh);
  return true;
}

async function request(path, { method = "GET", body, auth = true } = {}) {
  const doFetch = () =>
    fetch(`${BASE_URL}${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(auth ? authHeaders() : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });

  let res;
  try {
    res = await doFetch();
  } catch (e) {
    // Tarmoq/backend umuman javob bermadi (offline yoki server o'chirilgan) — buni
    // API xatoliklaridan (masalan 400/403) ajratib olish uchun alohida belgi qo'yamiz,
    // shunda UI "offline/demo rejim"ga muloyimlik bilan o'tishi mumkin.
    const err = new Error("Backend bilan aloqa yo'q (offline yoki server ishlamayapti)");
    err.isNetworkError = true;
    throw err;
  }
  if (res.status === 401 && auth) {
    const refreshed = await refreshAccessToken().catch(() => false);
    if (refreshed) res = await doFetch();
  }
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    let message = detail || res.statusText;
    try {
      const parsed = JSON.parse(detail);
      message = parsed.detail || Object.values(parsed).flat().join(" ") || message;
    } catch {
      // detail JSON emas — matn holicha qoladi
    }
    const err = new Error(message);
    err.status = res.status;
    throw err;
  }
  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

// ---- Backend health check (online/offline aniqlash uchun) ----
export async function pingBackend() {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 4000);
    const res = await fetch(`${BASE_URL}/subjects/`, { signal: controller.signal });
    clearTimeout(timeout);
    return res.ok || res.status === 401 || res.status === 403;
  } catch {
    return false;
  }
}

// ---- Auth ----
export const loginRequest = (username, password) =>
  request("/auth/login/", { method: "POST", body: { username, password }, auth: false });

export const registerRequest = (payload) =>
  request("/auth/register/", { method: "POST", body: payload, auth: false });

export const fetchMe = () => request("/auth/me/");
export const updateProfile = (payload) => request("/auth/me/", { method: "PATCH", body: payload });

// ---- Statistics ----
export const fetchDashboard = () => request("/statistics/dashboard/");

// ---- Subjects / Avatars ----
export const fetchSubjects = () => request("/subjects/", { auth: false });
export const fetchAvatars = () => request("/avatars/");

// ---- Sessions (avatar chat) ----
export const createSession = (subjectId, avatarId) =>
  request("/sessions/", { method: "POST", body: { subject: subjectId, avatar: avatarId } });
export const addSessionTurn = (sessionId, payload) =>
  request(`/sessions/${sessionId}/add_turn/`, { method: "POST", body: payload });
export const sendAvatarMessage = (sessionId, message) =>
  request(`/sessions/${sessionId}/chat/`, { method: "POST", body: { message } });
export const endSession = (sessionId) =>
  request(`/sessions/${sessionId}/end/`, { method: "POST" });

// ---- Math ----
export const fetchMathProblems = () => request("/math/problems/");
export const submitMathAnswer = (problemId, payload) =>
  request(`/math/problems/${problemId}/submit/`, { method: "POST", body: payload });

// ---- Flashcards ----
export const fetchDueFlashcards = () => request("/flashcards/reviews/due/");
export const gradeFlashcard = (reviewId, quality) =>
  request(`/flashcards/reviews/${reviewId}/grade/`, { method: "POST", body: { quality } });

// ---- Quiz (offlayn ishlaydi: savol+to'g'ri javob bir marta yuklab olingach localda tekshiriladi) ----
export const fetchQuizzes = () => request("/quizzes/");
export const submitQuizAttempt = (quizId, answers) =>
  request(`/quizzes/${quizId}/submit/`, { method: "POST", body: { answers } });

// ---- Flashcards: admin CRUD (AdminFlashcards.jsx tomonidan ishlatiladi) ----
export const fetchFlashcards = () => request("/flashcards/items/");
export const createFlashcard = (payload) => request("/flashcards/items/", { method: "POST", body: payload });
export const updateFlashcard = (id, payload) => request(`/flashcards/items/${id}/`, { method: "PATCH", body: payload });
export const deleteFlashcard = (id) => request(`/flashcards/items/${id}/`, { method: "DELETE" });

// ---- Leaderboard ----
export const fetchLeaderboard = (scope = "global_anon") => request(`/leaderboard/?scope=${scope}`);
export const fetchAdminLeaderboard = (scope = "global_anon") => request(`/leaderboard/?scope=${scope}&admin=1`);

// ---- YouTube AI Recommendations ----
export const fetchRecommendedVideos = (sessionId) =>
  request(`/youtube/recommendations/${sessionId ? "?session=" + sessionId : ""}`);
export const markVideoClicked = (recId) => request(`/youtube/recommendations/${recId}/click/`, { method: "POST" });
export const fetchSavedVideos = () => request("/youtube/saved/");
export const saveVideo = (videoId) => request("/youtube/saved/", { method: "POST", body: { video_id: videoId } });
export const rateVideo = (videoId, stars) => request("/youtube/ratings/", { method: "POST", body: { video: videoId, stars } });

// ---- AI Teacher: Lesson Generator + AI Chat ----
export const generateLesson = (subjectId, cefrLevelId) =>
  request("/ai-teacher/lessons/generate/", { method: "POST", body: { subject: subjectId, cefr_level: cefrLevelId } });
export const fetchLessons = () => request("/ai-teacher/lessons/");
export const fetchChatThreads = () => request("/ai-teacher/chat/");
export const createChatThread = (subjectId) => request("/ai-teacher/chat/", { method: "POST", body: { subject: subjectId } });
export const sendChatMessage = (threadId, message) =>
  request(`/ai-teacher/chat/${threadId}/send/`, { method: "POST", body: { message } });

// ---- Personalized Learning Path ----
export const fetchLearningPath = (subjectCode) => request(`/learning-path/${subjectCode ? "?subject=" + subjectCode : ""}`);
export const generateLearningPath = (subjectId) => request("/learning-path/generate/", { method: "POST", body: { subject: subjectId } });

// ---- Payments ----
export const fetchTransactions = () => request("/payments/transactions/");
export const createPayment = (planId, provider) =>
  request("/payments/transactions/", { method: "POST", body: { plan: planId, provider } });

// ---- Admin: Users ----
export const fetchAdminUsers = (search) => request(`/auth/admin/users/${search ? "?search=" + encodeURIComponent(search) : ""}`);
export const fetchAdminPayments = () => request("/payments/admin/transactions/");
export const fetchAdminVideos = () => request("/youtube/admin/videos/");
export const fetchAdminOverview = () => request("/statistics/admin/overview/");
export const createAdminUser = (payload) => request("/auth/admin/users/", { method: "POST", body: payload });
export const updateAdminUser = (id, payload) => request(`/auth/admin/users/${id}/`, { method: "PATCH", body: payload });
export const deleteAdminUser = (id) => request(`/auth/admin/users/${id}/`, { method: "DELETE" });
export const fetchPlans = () => request("/auth/plans/");

// ---- Admin: Subjects ----
export const createSubject = (payload) => request("/subjects/", { method: "POST", body: payload });
export const updateSubject = (id, payload) => request(`/subjects/${id}/`, { method: "PATCH", body: payload });
export const deleteSubject = (id) => request(`/subjects/${id}/`, { method: "DELETE" });

// ---- Admin: Avatars ----
export const createAvatarAdmin = (payload) => request("/avatars/", { method: "POST", body: payload });
export const updateAvatarAdmin = (id, payload) => request(`/avatars/${id}/`, { method: "PATCH", body: payload });
export const deleteAvatarAdmin = (id) => request(`/avatars/${id}/`, { method: "DELETE" });

// ---- Admin: Math problems ----
export const createMathProblem = (payload) => request("/math/problems/", { method: "POST", body: payload });
export const updateMathProblem = (id, payload) => request(`/math/problems/${id}/`, { method: "PATCH", body: payload });
export const deleteMathProblem = (id) => request(`/math/problems/${id}/`, { method: "DELETE" });

// ---- Admin: Videos ----
export const createAdminVideo = (payload) => request("/youtube/admin/videos/", { method: "POST", body: payload });
export const updateAdminVideo = (id, payload) => request(`/youtube/admin/videos/${id}/`, { method: "PATCH", body: payload });
export const deleteAdminVideo = (id) => request(`/youtube/admin/videos/${id}/`, { method: "DELETE" });

// ---- Admin: Payments ----
export const updateAdminPayment = (id, payload) => request(`/payments/admin/transactions/${id}/`, { method: "PATCH", body: payload });
export const deleteAdminPayment = (id) => request(`/payments/admin/transactions/${id}/`, { method: "DELETE" });

// ---- Integrations (LinkedIn Learning, Coursera, Khan Academy, Google Books) ----
export const fetchExternalCourses = (source) => request(`/integrations/courses/${source ? "?source=" + source : ""}`);
export const fetchSavedExternalCourses = () => request("/integrations/saved/");
export const saveExternalCourse = (courseId) => request("/integrations/saved/", { method: "POST", body: { course_id: courseId } });
