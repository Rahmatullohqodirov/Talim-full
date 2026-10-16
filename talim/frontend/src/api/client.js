const BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://localhost:8000/api/v1";

function authHeaders() {
  const token = localStorage.getItem("st_access_token");

  return token
    ? { Authorization: `Bearer ${token}` }
    : {};
}

async function refreshAccessToken() {
  const refresh =
    localStorage.getItem("st_refresh_token");

  if (!refresh) return false;

  const res = await fetch(
    `${BASE_URL}/auth/refresh/`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        refresh,
      }),
    }
  );

  if (!res.ok) return false;

  const data = await res.json();

  localStorage.setItem(
    "st_access_token",
    data.access
  );

  if (data.refresh) {
    localStorage.setItem(
      "st_refresh_token",
      data.refresh
    );
  }

  return true;
}

async function request(
  path,
  {
    method = "GET",
    body,
    auth = true,
  } = {}
) {
  const isForm =
    typeof FormData !== "undefined" &&
    body instanceof FormData;

  const doFetch = () =>
    fetch(`${BASE_URL}${path}`, {
      method,
      headers: {
        // FormData uchun Content-Type'ni brauzer o'zi (boundary bilan) qo'yadi
        ...(isForm ? {} : { "Content-Type": "application/json" }),
        ...(auth ? authHeaders() : {}),
      },
      body: isForm
        ? body
        : body
          ? JSON.stringify(body)
          : undefined,
    });

  let res;

  try {
    res = await doFetch();
  } catch (e) {
    const err = new Error(
      "Backend bilan aloqa yo'q (offline yoki server ishlamayapti)"
    );

    err.isNetworkError = true;

    throw err;
  }

  if (res.status === 401 && auth) {
    const refreshed =
      await refreshAccessToken().catch(
        () => false
      );

    if (refreshed) {
      res = await doFetch();
    }
  }

  if (!res.ok) {
    const detail =
      await res.text().catch(() => "");

    let message =
      detail || res.statusText;
    let parsedBody = null;

    try {
      const parsed = JSON.parse(detail);
      parsedBody = parsed;

      message =
        parsed.detail ||
        Object.values(parsed)
          .flat()
          .join(" ") ||
        message;
    } catch {
      // JSON emas — oddiy text
    }

    const err = new Error(message);

    err.status = res.status;
    err.data = parsedBody;

    throw err;
  }

  const text = await res.text();

  return text
    ? JSON.parse(text)
    : null;
}


// ======================================================
// Backend health check
// ======================================================

export async function pingBackend() {
  try {
    const controller =
      new AbortController();

    const timeout = setTimeout(
      () => controller.abort(),
      4000
    );

    const res = await fetch(
      `${BASE_URL}/subjects/`,
      {
        signal: controller.signal,
      }
    );

    clearTimeout(timeout);

    return (
      res.ok ||
      res.status === 401 ||
      res.status === 403
    );
  } catch {
    return false;
  }
}


// ======================================================
// Vocabulary
// ======================================================

export const fetchVocabularyLevels = () =>
  request(
    "/english-library/vocabulary/levels/"
  );


export const fetchVocabularyWords = (level, page = 1) => {
  console.log("🔥 fetchVocabularyWords level =", level);
  console.log("🔥 typeof level =", typeof level);

  const normalizedLevel = String(level || "")
    .trim()
    .toUpperCase();

  console.log("🔥 normalizedLevel =", normalizedLevel);

  if (!normalizedLevel) {
    throw new Error(
      "CEFR level mavjud emas. Kelgan qiymat: " +
        String(level)
    );
  }

  return request(
    `/english-library/vocabulary/?cefr=${encodeURIComponent(
      normalizedLevel
    )}&page=${page}&page_size=20`
  );
};


export const fetchVocabularyTest = (
  vocabularyId
) =>
  request(
    `/english-library/vocabulary/${vocabularyId}/test/`
  );


export const answerVocabulary = (
  vocabularyId,
  selectedId
) =>
  request(
    `/english-library/vocabulary/${vocabularyId}/answer/`,
    {
      method: "POST",
      body: {
        selected_id: selectedId,
      },
    }
  );


// ======================================================
// Auth
// ======================================================

export const loginRequest = (
  username,
  password
) =>
  request(
    "/auth/login/",
    {
      method: "POST",
      body: {
        username,
        password,
      },
      auth: false,
    }
  );


export const registerRequest = (
  payload
) =>
  request(
    "/auth/register/",
    {
      method: "POST",
      body: payload,
      auth: false,
    }
  );


export const verifyEmailRequest = (
  email,
  code
) =>
  request(
    "/auth/verify-email/",
    {
      method: "POST",
      body: {
        email,
        code,
      },
      auth: false,
    }
  );


export const resendCodeRequest = (
  email
) =>
  request(
    "/auth/resend-code/",
    {
      method: "POST",
      body: {
        email,
      },
      auth: false,
    }
  );


export const socialLoginRequest = (
  provider,
  token
) =>
  request(
    "/auth/social/",
    {
      method: "POST",
      body: {
        provider,
        token,
      },
      auth: false,
    }
  );


export const fetchMe = () =>
  request("/auth/me/");


export const updateProfile = (
  payload
) =>
  request(
    "/auth/me/",
    {
      method: "PATCH",
      body: payload,
    }
  );

// Profil sahifasi: hisob ma'lumotlari (ism, email, interfeys tili) va parol almashtirish
export const fetchAccount = () => request("/auth/me/account/");
export const updateAccount = (payload) => request("/auth/me/account/", { method: "PATCH", body: payload });
export const changePassword = (old_password, new_password) =>
  request("/auth/me/change-password/", { method: "POST", body: { old_password, new_password } });


// ======================================================
// Statistics
// ======================================================

export const fetchDashboard = () =>
  request(
    "/statistics/dashboard/"
  );


export const logActivity = (
  subjectCode,
  minutes,
  sessions = 1
) =>
  request(
    "/statistics/log-activity/",
    {
      method: "POST",
      body: {
        subject_code: subjectCode,
        minutes,
        sessions,
      },
    }
  );


// ======================================================
// Subjects / Avatars
// ======================================================

export const fetchSubjects = () =>
  request(
    "/subjects/",
    {
      auth: false,
    }
  );


export const fetchAvatars = () =>
  request("/avatars/");


// ======================================================
// Sessions
// ======================================================

export const createSession = (
  subjectId,
  avatarId,
  scenario = "free",
  fresh = false
) =>
  request(
    "/sessions/",
    {
      method: "POST",
      body: {
        subject: subjectId,
        avatar: avatarId,
        scenario,
        fresh,
      },
    }
  );

export const fetchScenarios = () => request("/sessions/scenarios/");


export const addSessionTurn = (
  sessionId,
  payload
) =>
  request(
    `/sessions/${sessionId}/add_turn/`,
    {
      method: "POST",
      body: payload,
    }
  );


export const sendAvatarMessage = (
  sessionId,
  message,
  accent = "american"
) =>
  request(
    `/sessions/${sessionId}/chat/`,
    {
      method: "POST",
      body: {
        message,
        accent,
      },
    }
  );


export const endSession = (
  sessionId
) =>
  request(
    `/sessions/${sessionId}/end/`,
    {
      method: "POST",
    }
  );


// ======================================================
// Math
// ======================================================

export const fetchMathProblems = () =>
  request("/math/problems/");


export const submitMathAnswer = (
  problemId,
  payload
) =>
  request(
    `/math/problems/${problemId}/submit/`,
    {
      method: "POST",
      body: payload,
    }
  );


// ======================================================
// Flashcards
// ======================================================

export const fetchDueFlashcards = () =>
  request(
    "/flashcards/reviews/due/"
  );


export const gradeFlashcard = (
  reviewId,
  quality
) =>
  request(
    `/flashcards/reviews/${reviewId}/grade/`,
    {
      method: "POST",
      body: {
        quality,
      },
    }
  );


// ======================================================
// Quiz
// ======================================================

export const fetchQuizzes = () =>
  request("/quizzes/");


export const submitQuizAttempt = (
  quizId,
  answers
) =>
  request(
    `/quizzes/${quizId}/submit/`,
    {
      method: "POST",
      body: {
        answers,
      },
    }
  );


// ======================================================
// Flashcards Admin CRUD
// ======================================================

export const fetchFlashcards = () =>
  request("/flashcards/items/");


export const createFlashcard = (
  payload
) =>
  request(
    "/flashcards/items/",
    {
      method: "POST",
      body: payload,
    }
  );


export const updateFlashcard = (
  id,
  payload
) =>
  request(
    `/flashcards/items/${id}/`,
    {
      method: "PATCH",
      body: payload,
    }
  );


export const deleteFlashcard = (
  id
) =>
  request(
    `/flashcards/items/${id}/`,
    {
      method: "DELETE",
    }
  );


// ======================================================
// Leaderboard
// ======================================================

export const fetchLeaderboard = (
  scope = "global_anon"
) =>
  request(
    `/leaderboard/?scope=${scope}`
  );


export const fetchAdminLeaderboard = (
  scope = "global_anon"
) =>
  request(
    `/leaderboard/?scope=${scope}&admin=1`
  );


// ======================================================
// YouTube AI Recommendations
// ======================================================

export const fetchRecommendedVideos = (
  sessionId
) =>
  request(
    `/youtube/recommendations/${
      sessionId
        ? "?session=" + sessionId
        : ""
    }`
  );


export const markVideoClicked = (
  recId
) =>
  request(
    `/youtube/recommendations/${recId}/click/`,
    {
      method: "POST",
    }
  );


export const fetchSavedVideos = () =>
  request(
    "/youtube/saved/"
  );


export const saveVideo = (
  videoId
) =>
  request(
    "/youtube/saved/",
    {
      method: "POST",
      body: {
        video_id: videoId,
      },
    }
  );


export const rateVideo = (
  videoId,
  stars
) =>
  request(
    "/youtube/ratings/",
    {
      method: "POST",
      body: {
        video: videoId,
        stars,
      },
    }
  );


// ======================================================
// AI Teacher
// ======================================================

export const generateLesson = (
  subjectId,
  cefrLevelId
) =>
  request(
    "/ai-teacher/lessons/generate/",
    {
      method: "POST",
      body: {
        subject: subjectId,
        cefr_level: cefrLevelId,
      },
    }
  );


export const fetchAiTeacherLessons = () =>
  request(
    "/ai-teacher/lessons/"
  );


export const fetchChatThreads = () =>
  request("/ai-teacher/chat/");

export const fetchChatThread = (threadId) =>
  request(`/ai-teacher/chat/${threadId}/`);

// subjectCode: "english" | "german" | "russian" | "turkish" | "uzbek" | "math" | null
export const createChatThread = (subjectCode) =>
  request("/ai-teacher/chat/", {
    method: "POST",
    body: subjectCode ? { subject_code_input: subjectCode } : {},
  });

export const updateChatThread = (threadId, payload) =>
  request(`/ai-teacher/chat/${threadId}/`, {
    method: "PATCH",
    body: payload,
  });

export const deleteChatThread = (threadId) =>
  request(`/ai-teacher/chat/${threadId}/`, {
    method: "DELETE",
  });

export const sendChatMessage = (threadId, message) =>
  request(`/ai-teacher/chat/${threadId}/send/`, {
    method: "POST",
    body: { message },
  });

// AI Ustoz xotirasi: o'quvchi haqida eslab qolingan faktlar
export const fetchTutorMemories = () =>
  request("/ai-teacher/memory/");

export const deleteTutorMemory = (id) =>
  request(`/ai-teacher/memory/${id}/`, { method: "DELETE" });

export const clearTutorMemories = () =>
  request("/ai-teacher/memory/clear/", { method: "POST" });

// Speaking: yozib olingan ovozni yuboradi -> {user_message, reply, audio_base64, weak_words}
export const sendSpeakingAudio = (threadId, blob, filename = "speech.webm") => {
  const form = new FormData();
  form.append("audio", blob, filename);
  return request(`/ai-teacher/chat/${threadId}/speak/`, {
    method: "POST",
    body: form,
  });
};


// ======================================================
// Personalized Learning Path
// ======================================================

export const fetchLearningPath = (
  subjectCode
) =>
  request(
    `/learning-path/${
      subjectCode
        ? "?subject=" + subjectCode
        : ""
    }`
  );


export const generateLearningPath = (
  subjectId
) =>
  request(
    "/learning-path/generate/",
    {
      method: "POST",
      body: {
        subject: subjectId,
      },
    }
  );


// ======================================================
// Payments
// ======================================================

export const fetchTransactions = () =>
  request(
    "/payments/transactions/"
  );


export const createPayment = (
  planId,
  provider
) =>
  request(
    "/payments/transactions/",
    {
      method: "POST",
      body: {
        plan: planId,
        provider,
      },
    }
  );


// ======================================================
// Admin: Users
// ======================================================

export const fetchAdminUsers = (
  search
) =>
  request(
    `/auth/admin/users/${
      search
        ? "?search=" +
          encodeURIComponent(search)
        : ""
    }`
  );


export const fetchAdminPayments = () =>
  request(
    "/payments/admin/transactions/"
  );


export const fetchAdminVideos = () =>
  request(
    "/youtube/admin/videos/"
  );


export const fetchAdminOverview = () =>
  request(
    "/statistics/admin/overview/"
  );


export const createAdminUser = (
  payload
) =>
  request(
    "/auth/admin/users/",
    {
      method: "POST",
      body: payload,
    }
  );


export const updateAdminUser = (
  id,
  payload
) =>
  request(
    `/auth/admin/users/${id}/`,
    {
      method: "PATCH",
      body: payload,
    }
  );


export const deleteAdminUser = (
  id
) =>
  request(
    `/auth/admin/users/${id}/`,
    {
      method: "DELETE",
    }
  );


export const fetchPlans = () =>
  request(
    "/auth/plans/"
  );


// ======================================================
// Admin: Subjects
// ======================================================

export const createSubject = (
  payload
) =>
  request(
    "/subjects/",
    {
      method: "POST",
      body: payload,
    }
  );


export const updateSubject = (
  id,
  payload
) =>
  request(
    `/subjects/${id}/`,
    {
      method: "PATCH",
      body: payload,
    }
  );


export const deleteSubject = (
  id
) =>
  request(
    `/subjects/${id}/`,
    {
      method: "DELETE",
    }
  );


// ======================================================
// Admin: Avatars
// ======================================================

export const createAvatarAdmin = (
  payload
) =>
  request(
    "/avatars/",
    {
      method: "POST",
      body: payload,
    }
  );


export const updateAvatarAdmin = (
  id,
  payload
) =>
  request(
    `/avatars/${id}/`,
    {
      method: "PATCH",
      body: payload,
    }
  );


export const deleteAvatarAdmin = (
  id
) =>
  request(
    `/avatars/${id}/`,
    {
      method: "DELETE",
    }
  );


// ======================================================
// Admin: Math Problems
// ======================================================

export const createMathProblem = (
  payload
) =>
  request(
    "/math/problems/",
    {
      method: "POST",
      body: payload,
    }
  );


export const updateMathProblem = (
  id,
  payload
) =>
  request(
    `/math/problems/${id}/`,
    {
      method: "PATCH",
      body: payload,
    }
  );


export const deleteMathProblem = (
  id
) =>
  request(
    `/math/problems/${id}/`,
    {
      method: "DELETE",
    }
  );


// ======================================================
// Admin: Videos
// ======================================================

export const createAdminVideo = (
  payload
) =>
  request(
    "/youtube/admin/videos/",
    {
      method: "POST",
      body: payload,
    }
  );


export const updateAdminVideo = (
  id,
  payload
) =>
  request(
    `/youtube/admin/videos/${id}/`,
    {
      method: "PATCH",
      body: payload,
    }
  );


export const deleteAdminVideo = (
  id
) =>
  request(
    `/youtube/admin/videos/${id}/`,
    {
      method: "DELETE",
    }
  );


// ======================================================
// Admin: Payments
// ======================================================

export const updateAdminPayment = (
  id,
  payload
) =>
  request(
    `/payments/admin/transactions/${id}/`,
    {
      method: "PATCH",
      body: payload,
    }
  );


export const deleteAdminPayment = (
  id
) =>
  request(
    `/payments/admin/transactions/${id}/`,
    {
      method: "DELETE",
    }
  );


// ======================================================
// Integrations
// ======================================================

export const fetchExternalCourses = (
  source
) =>
  request(
    `/integrations/courses/${
      source
        ? "?source=" + source
        : ""
    }`
  );


export const fetchSavedExternalCourses = () =>
  request(
    "/integrations/saved/"
  );


export const saveExternalCourse = (
  courseId
) =>
  request(
    "/integrations/saved/",
    {
      method: "POST",
      body: {
        course_id: courseId,
      },
    }
  );

// ======================================================
// Yangi bo'limlar (Dashboard, reja, quiz, flashcard, vocabulary, video, ovoz)
// ======================================================

const qs = (params = {}) => {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "");
  return entries.length ? "?" + new URLSearchParams(entries).toString() : "";
};

// O'quv rejalari
export const fetchStudyPlans = () => request("/ai-teacher/plans/");
export const toggleStudyPlanItem = (planId, itemId, done) =>
  request(`/ai-teacher/plans/${planId}/toggle/`, { method: "POST", body: { item_id: itemId, done } });
export const deleteStudyPlan = (planId) =>
  request(`/ai-teacher/plans/${planId}/`, { method: "DELETE" });

// AI Ustoz holati va ovozli suhbat
export const fetchTutorStatus = () => request("/ai-teacher/status/");
export const sendVoiceAudio = (threadId, blob, filename = "voice.webm") => {
  const form = new FormData();
  form.append("audio", blob, filename);
  return request(`/ai-teacher/chat/${threadId}/voice/`, { method: "POST", body: form });
};

// Leaderboard: period = week | month | all
export const fetchLeaderboardPeriod = (period = "week") =>
  request(`/leaderboard/${qs({ period })}`);

// Quiz
export const fetchQuizLevels = (subject = "english") =>
  request(`/quizzes/levels/${qs({ subject })}`);
export const fetchQuizList = (params = {}) => request(`/quizzes/${qs(params)}`);
export const fetchQuiz = (id) => request(`/quizzes/${id}/`);

// Flashcard
export const fetchFlashcardSession = (params = {}) =>
  request(`/flashcards/reviews/session/${qs(params)}`);
export const fetchFlashcardStats = () => request("/flashcards/reviews/stats/");

// Vocabulary
export const fetchVocabularySession = (level, size = 10) =>
  request(`/english-library/vocabulary/session/${qs({ cefr: level, size })}`);
export const fetchVocabularyList = (params = {}) =>
  request(`/english-library/vocabulary/${qs(params)}`);
export const answerVocabularyWord = (id, correct) =>
  request(`/english-library/vocabulary/${id}/answer/`, { method: "POST", body: { correct } });
export const markVocabularyKnown = (id) =>
  request(`/english-library/vocabulary/${id}/known/`, { method: "POST" });

// YouTube qidiruv
export const searchYoutube = (q, duration) =>
  request(`/youtube/search/${qs({ q, duration })}`);
export const addWatchHistory = (videoId) =>
  request("/youtube/history/", { method: "POST", body: { video: videoId } });
export const removeSavedVideo = (savedId) =>
  request(`/youtube/saved/${savedId}/`, { method: "DELETE" });

// Google/Facebook ID'lari (backend .env dan) — frontendda alohida sozlash shart emas
export const fetchSocialConfig = () =>
  request("/auth/social/config/", { auth: false });

// Lug'at
export const searchDictionary = (q) =>
  request(`/english-library/dictionary/${q ? "?q=" + encodeURIComponent(q) : ""}`);
export const addWordToLearning = (id) =>
  request(`/english-library/vocabulary/${id}/learn/`, { method: "POST" });

// Matematika
export const fetchMathProgress = () => request("/math/problems/progress/");
export const explainMathProblem = (id) =>
  request(`/math/problems/${id}/ai_explain/`, { method: "POST" });

// Obuna
export const fetchSubscriptionStatus = () => request("/payments/status/");

// Admin: murojaatlar, tariflar, quizlar
export const fetchAdminTickets = (status) => request(`/ai-teacher/admin/tickets/${status ? "?status=" + status : ""}`);
export const updateAdminTicket = (id, payload) => request(`/ai-teacher/admin/tickets/${id}/`, { method: "PATCH", body: payload });
export const fetchAdminPlans = () => request("/payments/admin/plans/");
export const createAdminPlan = (payload) => request("/payments/admin/plans/", { method: "POST", body: payload });
export const updateAdminPlan = (id, payload) => request(`/payments/admin/plans/${id}/`, { method: "PATCH", body: payload });
export const deleteAdminPlan = (id) => request(`/payments/admin/plans/${id}/`, { method: "DELETE" });
export const publishQuiz = (id, is_published) => request(`/quizzes/${id}/publish/`, { method: "POST", body: { is_published } });
export const rebuildQuiz = (id) => request(`/quizzes/${id}/rebuild/`, { method: "POST" });

// Darslar (grammatika + so'z lug'ati + mashqlar)
export const fetchLessons = (subject, level) => request(`/lessons/${qs({ subject, level })}`);
export const fetchLesson = (id) => request(`/lessons/${id}/`);
export const submitLesson = (id, answers) => request(`/lessons/${id}/submit/`, { method: "POST", body: { answers } });

// Tinglang va o'qing (hikoyalar kutubxonasi)
export const fetchStories = (subject, level) => request(`/stories/${qs({ subject, level })}`);
export const fetchStory = (id) => request(`/stories/${id}/`);
export const submitStory = (id, answers) => request(`/stories/${id}/submit/`, { method: "POST", body: { answers } });

// Admin: darslar va hikoyalar
export const fetchAdminLessons = (params = {}) => request(`/admin/lessons/${qs(params)}`);
export const createAdminLesson = (payload) => request("/admin/lessons/", { method: "POST", body: payload });
export const updateAdminLesson = (id, payload) => request(`/admin/lessons/${id}/`, { method: "PATCH", body: payload });
export const deleteAdminLesson = (id) => request(`/admin/lessons/${id}/`, { method: "DELETE" });
export const generateAdminLessons = (subject, level) =>
  request("/admin/lessons/generate/", { method: "POST", body: { subject, level } });

export const fetchAdminStories = (params = {}) => request(`/admin/stories/${qs(params)}`);
export const createAdminStory = (payload) => request("/admin/stories/", { method: "POST", body: payload });
export const updateAdminStory = (id, payload) => request(`/admin/stories/${id}/`, { method: "PATCH", body: payload });
export const deleteAdminStory = (id) => request(`/admin/stories/${id}/`, { method: "DELETE" });
export const generateAdminStories = (subject, level) =>
  request("/admin/stories/generate/", { method: "POST", body: { subject, level } });
