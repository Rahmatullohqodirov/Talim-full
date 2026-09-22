export const overallCards = [
  { label: "Umumiy soat", value: "48.5" },
  { label: "Sessiyalar", value: "132" },
  { label: "Umumiy ball", value: "2,340" },
  { label: "Streak", value: "🔥 14 kun" },
];

export const subjectStats = [
  { name: "Ingliz tili", level: "B1", minutes: 620, sessions: 84, pronunciation: 82, streak: 14 },
  { name: "Matematika", level: "8-sinf", minutes: 340, sessions: 48, pronunciation: 0, streak: 6 },
];

export const heatmapCells = Array.from({ length: 98 }, (_, i) => {
  const seed = (i * 37) % 11;
  const intensity = seed < 4 ? 0 : seed < 6 ? 1 : seed < 8 ? 2 : seed < 10 ? 3 : 4;
  const colors = ["oklch(0.95 0.005 260)", "oklch(0.88 0.05 275)", "oklch(0.75 0.12 275)", "oklch(0.62 0.17 275)", "oklch(0.5 0.19 275)"];
  return { color: colors[intensity] };
});

export const initialChatMessages = [
  { id: 1, text: "Hi! Ready to practice today? Tell me about your weekend.", mine: false },
  { id: 2, text: "Yes, I go to park with my friends yesterday.", mine: true, pronunciation: 82, grammar: 74 },
  { id: 3, text: "Nice! Small correction: “I went to the park” — past tense. Try again?", mine: false },
];

export const mathProblems = [
  { topic: "Kvadrat tenglamalar", difficulty: "O'rta", statement: "x² - 5x + 6 = 0 tenglamani yeching.", answer: "2,3", steps: ["x² - 5x + 6 = 0", "(x-2)(x-3) = 0", "x = 2 yoki x = 3"] },
  { topic: "Chiziqli tenglamalar", difficulty: "Oson", statement: "3x + 7 = 22 tenglamani yeching.", answer: "5", steps: ["3x + 7 = 22", "3x = 15", "x = 5"] },
];

export const weakTopics = [
  { name: "Kvadrat tenglamalar", accuracy: 54 },
  { name: "Trigonometriya", accuracy: 61 },
  { name: "Hosila", accuracy: 47 },
];

export const flashcards = [
  { front: "Ubiquitous", back: "Har yerda mavjud bo'lgan" },
  { front: "Resilient", back: "Chidamli, bardoshli" },
  { front: "Meticulous", back: "Puxta, sinchkov" },
];

export const leaderboard = [
  { rank: 1, name: "Diyorbek", points: 3120, you: false },
  { rank: 2, name: "Aziz (siz)", points: 2340, you: true },
  { rank: 3, name: "Malika", points: 2100, you: false },
  { rank: 4, name: "Sardor", points: 1980, you: false },
  { rank: 5, name: "Nodira", points: 1750, you: false },
];

export const adminUsers = [
  { name: "Aziz Karimov", email: "aziz@example.com", subject: "Ingliz", level: "B1", premium: true },
  { name: "Malika Yusupova", email: "malika@example.com", subject: "Matematika", level: "9-sinf", premium: false },
  { name: "Sardor Rashidov", email: "sardor@example.com", subject: "Nemis", level: "A2", premium: false },
  { name: "Nodira Tosheva", email: "nodira@example.com", subject: "Turk", level: "A1", premium: true },
];

export const adminSubjects = [
  { name: "Ingliz tili", kind: "Til", levels: 6, active: true },
  { name: "Matematika", kind: "Fan", levels: 12, active: true },
  { name: "Rus tili", kind: "Til", levels: 6, active: false },
  { name: "Nemis tili", kind: "Til", levels: 6, active: false },
  { name: "Turk tili", kind: "Til", levels: 6, active: false },
];

export const adminAvatars = [
  { name: "Emma", gender: "Ayol", premium: false },
  { name: "Alex", gender: "Erkak", premium: false },
  { name: "Sofia", gender: "Ayol", premium: true },
  { name: "Marcus", gender: "Erkak", premium: true },
];

export const adminProblems = [
  { topic: "Kvadrat tenglamalar", statement: "x² - 5x + 6 = 0", difficulty: "O'rta" },
  { topic: "Chiziqli tenglamalar", statement: "3x + 7 = 22", difficulty: "Oson" },
  { topic: "Trigonometriya", statement: "sin(x) = 0.5, x = ?", difficulty: "Qiyin" },
];

export const adminStatCards = [
  { label: "Jami foydalanuvchilar", value: "4,812" },
  { label: "Faol premium", value: "612" },
  { label: "Bugungi sessiyalar", value: "318" },
  { label: "O'rtacha streak", value: "9 kun" },
];

export const recommendedVideos = [
  { id: 1, title: "Present Perfect Tense Explained", channel: "EnglishClass101", duration: "8:24", difficulty: "B1", rating: 4.7 },
  { id: 2, title: "Quadratic Equations — Full Walkthrough", channel: "Khan Academy", duration: "12:10", difficulty: "O'rta", rating: 4.9 },
  { id: 3, title: "Common Pronunciation Mistakes (TH sound)", channel: "Rachel's English", duration: "6:45", difficulty: "A2-B1", rating: 4.6 },
];

export const savedVideos = [
  { id: 2, title: "Quadratic Equations — Full Walkthrough", channel: "Khan Academy", duration: "12:10" },
];

export const aiChatMessages = [
  { id: 1, role: "assistant", text: "Salom! Men Talim repetitoringizman. Nimada yordam bera olaman?" },
];

export const paymentPlans = [
  { id: 1, name: "Premium (oylik)", price: "$9", provider: "payme" },
  { id: 2, name: "Premium (yillik)", price: "$79", provider: "click" },
];

export const transactionHistory = [
  { id: 1, plan: "Premium (oylik)", provider: "Payme", amount: "114,300 so'm", status: "success", date: "2026-07-01" },
];

export const adminVideos = [
  { title: "Present Perfect Tense Explained", subject: "Ingliz", difficulty: "B1", rating: 4.7, views: 12400 },
  { title: "Quadratic Equations — Full Walkthrough", subject: "Matematika", difficulty: "O'rta", rating: 4.9, views: 8600 },
  { title: "Common Pronunciation Mistakes", subject: "Ingliz", difficulty: "A2-B1", rating: 4.6, views: 5200 },
];

export const adminPayments = [
  { user: "Aziz Karimov", plan: "Premium (oylik)", provider: "Payme", amount: "114,300 so'm", status: "success", date: "2026-07-20" },
  { user: "Nodira Tosheva", plan: "Premium (yillik)", provider: "Click", amount: "1,003,300 so'm", status: "success", date: "2026-07-18" },
  { user: "Sardor Rashidov", plan: "Premium (oylik)", provider: "Payme", amount: "114,300 so'm", status: "pending", date: "2026-07-25" },
];

export const externalCourses = [
  { id: 1, source: "linkedin_learning", source_label: "LinkedIn Learning", title: "Communicating with Confidence", level: "Boshlang'ich", is_premium_only: true, url: "#" },
  { id: 2, source: "linkedin_learning", source_label: "LinkedIn Learning", title: "Business English Fundamentals", level: "O'rta", is_premium_only: true, url: "#" },
  { id: 3, source: "coursera", source_label: "Coursera", title: "Calculus: Single Variable", level: "Ilg'or", is_premium_only: false, url: "#" },
  { id: 4, source: "khan_academy", source_label: "Khan Academy", title: "Algebra I to'liq kurs", level: "Boshlang'ich", is_premium_only: false, url: "#" },
  { id: 5, source: "google_books", source_label: "Google Books", title: "English Grammar in Use", level: "B1-B2", is_premium_only: false, url: "#" },
];
