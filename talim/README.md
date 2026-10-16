# Talim — Full Stack

Bitta papkada backend (Django) va frontend (React) birga.

## Struktura
- `backend/` — Django REST API (talim)
- `frontend/` — React (Vite) ilova, admin panel + PWA (offline) qo'llab-quvvatlash bilan

## Ishga tushirish (lokal kompyuteringizda, faqat SQLite — Postgres/Redis shart emas)

### 1. Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate       # Windows
# yoki: source .venv/bin/activate   # macOS/Linux
pip install -r requirements/base.txt
copy .env .env       # yoki: cp .env .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Backend: http://localhost:8000
Admin panelga kirish uchun `createsuperuser` bilan yaratgan hisobingizdan (is_staff=True) frontendda login qiling — tizim avtomatik admin panelga yo'naltiradi.

> Eslatma: `config/settings/dev.py` Redis/Postgres talab qilmaydi — cache xotirada (locmem),
> Celery vazifalari darhol bajariladi (eager), Channels xotirada ishlaydi. Productionga
> chiqarganda `config/settings/prod.py` va haqiqiy Redis/Postgres sozlamalaridan foydalaning.

### 2. Frontend (alohida terminalda)
```bash
cd frontend
npm install
copy .env .env       # yoki: cp .env .env
npm run dev
```
Frontend: http://localhost:5173

Ikkalasi ham bir vaqtda ishlab turishi kerak (backend 8000-portda, frontend 5173-portda).

## Admin panel

`/app/admin` (backend orqali is_staff=True bo'lgan foydalanuvchi kirganda avtomatik ochiladi) —
foydalanuvchilar, fanlar, avatarlar, matematik masalalar, video kutubxonasi va to'lovlarni
**to'liq qo'shish / tahrirlash / o'chirish** imkoniyati bilan. Barcha bo'limlar haqiqiy
backend API'ga ulangan.

## Onlayn / Oflayn ishlash

- **Backend bilan bog'lanish uzilsa** (server o'chirilgan yoki internet yo'q): frontend
  avtomatik ravishda demo (namunaviy) ma'lumotlarni ko'rsatishga o'tadi va sidebar/admin
  panelda "Offlayn (demo)" indikatori chiqadi. Ilova ishlashda davomida qoladi, faqat
  o'zgarishlarni saqlash uchun backend qayta ulanishi kerak.
- **PWA (Progressive Web App)**: frontend `vite-plugin-pwa` bilan sozlangan — brauzerda
  bir marta ochilgach, ilovaning o'zi (HTML/JS/CSS) va so'nggi ko'rilgan API javoblari
  keshlanadi, shu sabab internet umuman bo'lmasa ham ilova ochiladi. Chrome/Edge'da manzil
  qatoridagi "O'rnatish" tugmasi orqali ilovani telefon/kompyuteringizga o'rnatishingiz ham
  mumkin (`npm run build` + `npm run preview` bilan production rejimida eng yaxshi ishlaydi,
  chunki service worker faqat build qilingan versiyada faol).

## Production uchun eslatma

Bu sozlama faqat lokal ishlab chiqish uchun (SQLite, DEBUG=True). Serverga joylashtirishda:
1. `config/settings/prod.py`ni ishlating (`DJANGO_SETTINGS_MODULE=config.settings.prod`)
2. Haqiqiy Postgres va Redis manzillarini `.env`da ko'rsating
3. `SECRET_KEY`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`ni production qiymatlariga o'zgartiring
