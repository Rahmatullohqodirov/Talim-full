# SuperTutor AI — React Frontend

Vite + React + React Router, **backendga ulangan** (`supertutor_ai` Django API). Backend ishlamasa yoki CORS/404 bo'lsa, sahifalar avtomatik demo (mock) ma'lumotga tushadi — UI hech qachon buzilmaydi.

## Ishga tushirish

```bash
npm install
cp .env .env   # VITE_API_BASE_URL ni backend manzilingizga moslang
npm run dev
```

Backendni ishga tushirish uchun `supertutor_ai/README.md`ga qarang (odatda http://localhost:8000).

## Backendga ulangan qismlar
- Login / Register — `/auth/login/`, `/auth/register/` (JWT `localStorage`da saqlanadi)
- Dashboard — `/statistics/dashboard/`
- Matematika mashqlari — `/math/problems/` + `submit`
- Leaderboard — `/leaderboard/`

Hali mock: Avatar chat (sessions API tayyor, real-time ovoz oqimi backendda yo'q), Flashcard, va Admin panel (backendda umumiy ro'yxat/CRUD endpointlar hali yo'q — `supertutor_ai` ustida qo'shish kerak).

## Struktura
- `src/api/client.js` — barcha backend chaqiruvlari
- `src/context/AppContext.jsx` — auth holati (token) + student/admin demo-rol
- `src/pages/app/` — ilova ekranlari
- `src/pages/admin/` — admin panel (sidebar nav, jadval/kartalar)
- `src/data/mockData.js` — backend mavjud bo'lmaganda ishlatiladigan demo ma'lumot
