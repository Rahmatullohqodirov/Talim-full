# Talim — backendga moslangan funksiyalar

Tuzatilgan qismlar:
- Leaderboard — real `/api/v1/leaderboard/` dan olinadi, haftalik rank qayta hisoblanadi.
- Video tavsiyalar — `/api/v1/youtube/recommendations/` va saved videolar bilan ishlaydi; demo/mock fallback olib tashlandi.
- Flashcard Spaced Repetition — yangi foydalanuvchi uchun due review avtomatik yaratiladi va SM-2 uslubidagi grade saqlanadi.
- Matematika — backend `solution_steps`, `topic_name` va `difficulty_label` qaytaradi; javob `/submit/` orqali tekshiriladi.
- 5 ta fan — Ingliz tili, Matematika, Rus tili, Nemis tili, Turk tili seed orqali faol qilinadi.
- Avatar bilan ingliz tili suhbati — `/api/v1/sessions/{id}/chat/` orqali AI javobi backendda yaratiladi va transcript sifatida saqlanadi.
- Admin — Flashcard CRUD va Leaderboard ko'rish bo'limlari qo'shildi; mavjud Users/Subjects/Avatars/Problems/Videos/Payments/Stats bo'limlari backendga ulandi.

## Ishga tushirish

### Backend
```powershell
cd talim	alimackend
python manage.py migrate
python manage.py seed_initial_data
# Agar YouTube katalogi ham kerak bo'lsa:
python manage.py shell -c "exec(open('scripts/seed_more.py', encoding='utf-8').read())"
python manage.py runserver
```

### Frontend
```powershell
cd talim	alimrontend
npm install
npm run dev
```

Frontend `.env`:
```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

`node_modules` zipga ataylab qo'shilmadi: Windows/WSL platforma aralashib, Vite/Rollup native paketlarida xato bermasligi uchun `npm install`ni lokal kompyuterda qayta bajarish kerak.

AI avatar javobi uchun backend `.env`da `GROQ_API_KEY` yoki `XAI_API_KEY` bo'lishi kerak. Kalit bo'lmasa backend offline fallback javob beradi.
