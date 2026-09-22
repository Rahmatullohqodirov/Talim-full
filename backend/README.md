# Talim — Backend

Django + DRF backend. MVP scope: English + Math, full statistics dashboard, single avatar.

## Setup
```
pip install -r requirements/base.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

## AI Chat / Lesson Generator (xAI Grok)

`apps/ai_teacher` AI Chat va Lesson Generator uchun **xAI Grok**dan (`/v1/responses`) foydalanadi.
Ishlashi uchun `.env`da `XAI_API_KEY`ni kiriting (https://console.x.ai dan olinadi):
```
XAI_API_KEY=xai-...
XAI_MODEL=grok-4.6   # ixtiyoriy, default shu
```
- `XAI_API_KEY` bo'lmasa yoki Grok javob bermasa → avtomatik `GROQ_API_KEY` (agar bor bo'lsa) bilan zaxira provayderga o'tadi.
- Hech qanday kalit bo'lmasa yoki internet yo'q bo'lsa → xatoga chiqmasdan offline demo javob qaytaradi, ilova ishlashda davom etadi.

Apps: accounts, subjects, sessions, statistics, math_practice, avatars, gamification, learning_path, practice_tools, ai_teacher.
