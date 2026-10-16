# O'zgarishlar jurnali — 2026-09-17

Ushbu faylda joriy seansda kiritilgan barcha o'zgarishlar ro'yxati keltirilgan.

## 1. Kontent (Flashcard / Quiz / Matematika)
- **Muammo**: Flashcard bo'limi "5 tadan keyin tugab qolar edi" — sabab bug emas, bazada
  jami 5 ta karta bor edi.
- **Yechim**: `backend/apps/subjects/management/commands/seed_bulk_content.py` qo'shildi —
  187 ta flashcard, 32 ta quiz savoli, 26 ta matematik masala. Ishga tushirish:
  `python manage.py seed_bulk_content` (xavfsiz, qayta ishga tushirsa ham dublikat yaratmaydi).
- Namunaviy `db.sqlite3` fayliga bu ma'lumotlar allaqachon qo'shib qo'yilgan — zipni ochib,
  darhol sinab ko'rishingiz mumkin.

## 2. Dashboard statistikasi (kunlik / haftalik / oylik / yillik)
- **Muammo**: `DailyActivity` yozuvlari umuman yaratilmas edi (0 ta qator), shuning uchun
  dashboarddagi heatmap va haftalik o'sish foizi **doim mock (qalbaki)** ma'lumot ko'rsatar edi.
- **Yechim**:
  - `backend/apps/statistics/tasks.py` — `recompute_subject_stats` endi har bir sessiyadan
    so'ng `DailyActivity` yozuvini yaratadi/yangilaydi va streakni hisoblaydi.
  - `backend/apps/statistics/views.py` — yangi `series` maydoni: kunlik (30 kun), haftalik
    (12 hafta), oylik (12 oy), yillik (5 yil) real vaqt-seriyali statistika.
  - `frontend/src/pages/app/Dashboard.jsx` — davr tanlovchi (Kunlik/Haftalik/Oylik/Yillik)
    tugmalar va shu ma'lumotlarni chizuvchi (kutubxonasiz, sof CSS) ustunli grafik qo'shildi;
    heatmap va o'sish foizi endi haqiqiy API ma'lumotidan olinadi.

## 3. To'lov (Billing)
- **Muammo 1**: Payme/Click provayderini tanlab bo'lmas edi — kod doim `"payme"` deb
  yozilgan edi.
- **Muammo 2**: To'lovlar tarixi hech qachon haqiqiy API'dan yuklanmas edi — doim mock
  ma'lumot ko'rsatilardi.
- **Yechim**: `frontend/src/pages/app/Billing.jsx` — har bir reja uchun Payme/Click tanlash
  tugmalari, va `fetchTransactions()` orqali haqiqiy tarix yuklanadi (backend ulanmasa,
  buni foydalanuvchiga ochiq bildiradi). `PaymentTransactionSerializer`ga `plan_name`
  qo'shildi.

## 4. Xavfsizlik
- `backend/config/settings/prod.py`: HSTS, secure cookie, `SECURE_PROXY_SSL_HEADER`,
  clickjacking himoyasi (`X_FRAME_OPTIONS`), `CSRF_TRUSTED_ORIGINS`, Sentry monitoring
  ulash, `SECRET_KEY`/`ALLOWED_HOSTS` bo'sh bo'lsa serverni ishga tushirmaslik (xato chiqarish).
- `backend/config/settings/base.py`: login/registratsiya (`auth`) va to'lov (`payment`)
  endpointlariga brute-force/spam himoyasi uchun rate-limit (`ScopedRateThrottle`) qo'shildi.
- `.env.example` — production uchun to'liq namunaviy sozlamalar fayli yaratildi.
- `.gitignore` — `.env`, `db.sqlite3`, `node_modules/` va h.k. endi tasodifan
  git/zip'ga tushib qolmaydi.
- ⚠️ **MUHIM**: yuklangan zipdagi `.env` faylida haqiqiy YouTube va Groq API kalitlari
  ochiq holda bor edi. Ikkalasini ham darhol bekor qilib, yangisini oling.

## 5. AI Chat — ovozli rejim (avatar/orb)
- `frontend/src/pages/app/AIChat.jsx` va `AIChat.css` — mikrofon tugmasi bosilganda
  to'liq ekranli, qora fonli, porlab turadigan gradient orb ochiladi (yuborgan rasmlaringizga
  o'xshab). Orb holatga qarab rangi/animatsiyasi o'zgaradi: idle (moviy, sokin nafas olish),
  listening (tezroq pulsatsiya), thinking (to'q sariq, aylanuvchi), speaking (yashil, tez pulsatsiya).
  Brauzerning o'z ovoz tanish (`SpeechRecognition`) va ovozli javob (`speechSynthesis`)
  imkoniyatlaridan foydalanadi — qo'shimcha to'lovli AI-ovoz xizmatiga ehtiyoj yo'q.

## 6. Offline Quiz mashqi (yangi bo'lim)
- **Aniqlangan muammo**: talaba uchun umuman quiz yechish sahifasi yo'q edi (faqat admin
  uchun CRUD bor edi).
- **Yechim**: yangi `frontend/src/pages/app/QuizPractice.jsx` sahifasi + `/app/quiz` route +
  sidebar'ga "Quiz" bandi qo'shildi.
  - Savol va to'g'ri javoblar bir marta yuklab olingach, **to'liq offlayn** ishlaydi
    (natija darhol, lokal hisoblanadi).
  - Internet bo'lmaganda natija brauzerda saqlanib qoladi va ulanish tiklangach avtomatik
    serverga yuboriladi.
  - Backend: `Quiz` ViewSet'ga `submit` action qo'shildi — ball serverda qayta tekshiriladi
    (xavfsizlik uchun), `QuizAttempt` sifatida saqlanadi.

## Sizga qolgan ishlar (men bajarolmaydigan narsalar)
1. **Haqiqiy domenga chiqarish** — server sotib olish/ijaraga olish, DNS, SSL sertifikat
   sozlash (masalan Nginx + Let's Encrypt). Buni sizning serveringizda bajarish kerak.
2. **Payme/Click bilan haqiqiy shartnoma** — ularning biznes-kabinetidan ro'yxatdan o'tib,
   `PAYME_MERCHANT_ID`/`CLICK_MERCHANT_ID` kalitlarini oling va `.env` fayliga qo'ying.
3. **API kalitlarini yangilash** — yuqorida aytilganidek, eski YouTube/Groq kalitlarini
   bekor qiling.
4. `npm install` — frontend'da yangi kutubxona qo'shilmagan, lekin `node_modules` zipga
   kiritilmagan, shuning uchun frontendni ishga tushirishdan oldin `npm install` kerak.
