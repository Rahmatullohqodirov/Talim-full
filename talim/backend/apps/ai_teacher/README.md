# AI Ustoz (ai_teacher)

AI Ustoz Claude orqali ishlaydi va o'quvchining haqiqiy ma'lumotlari bilan tool'lar yordamida ishlay oladi.

## Ishga tushirish

```bash
cd backend
pip install -r requirements/base.txt
python manage.py migrate
```

`.env` fayliga qo'shing:

```
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-5-5
```

Kalit bo'lmasa yoki Claude javob bermasa, tizim avtomatik ravishda eski zanjirga o'tadi: xAI Grok, keyin Groq, keyin offline javob.
Bu holda tool'lar ishlamaydi va model daraja yoki statistikani ko'ra olmaydi.

### Speaking (ixtiyoriy)

```bash
pip install -r requirements/speaking.txt
```

Birinchi so'rovda Whisper modeli (~500 MB, `small`) internetdan yuklab olinadi. Kuchsiz serverda `WHISPER_MODEL_SIZE=base` qo'ying.
Paket o'rnatilmagan bo'lsa, `/speak/` 501 qaytaradi va frontend brauzerning o'z ovoz tanish funksiyasiga o'tadi.

## Fayllar

| Fayl | Vazifasi |
|---|---|
| `prompts.py` | Tizim promptlari va `APP_FAQ` (ilova haqidagi faktlar, **o'zingiz to'ldiring**) |
| `tools.py` | 13 ta tool. `user_id` modelga berilmaydi, har doim `request.user` ishlatiladi |
| `agent.py` | Claude tool sikli, prompt caching, tarixni cheklash |
| `learner.py` | O'quvchi kartasi: har so'rovda Claude'ga beriladigan profil (xotira, darajalar, natijalar, darslar) |
| `speaking.py` | Whisper, Claude (`<speak>` + `<feedback>`), edge-tts |
| `services.py` | `chat_with_ai`, `call_ai` (matematika va avatar ham shu funksiyadan foydalanadi) |

## O'quvchini eslab qolish

Har bir o'quvchi uchun `LearnerMemory` jadvalida o'qishga oid faktlar saqlanadi: qiziqish, maqsad,
o'rganish uslubi, takrorlanadigan xato va kuchli tomon. Ustoz ularni o'zi `remember_about_student`
tool'i bilan saqlaydi. Har so'rovda ular darajalar, oxirgi natijalar va darslar bilan birga
"o'quvchi kartasi" sifatida Claude'ga beriladi. Shu sababli yangi suhbatda ham Ustoz o'quvchini taniydi.

- Bitta o'quvchi uchun ko'pi bilan 50 ta fakt saqlanadi, eng eskilari avtomatik o'chadi.
- Telefon raqami, email, havola va karta raqami serverda rad etiladi. Sog'liq, oila va manzil
  haqidagi ma'lumotni saqlamaslik promptda yozilgan.
- O'quvchi "Ustoz xotirasi" panelida faktlarni ko'radi va o'chiradi. Admin ham ularni ko'ra oladi.

## Dars o'tish

`start_lesson` → `update_lesson_progress` (har qadamdan keyin) → `finish_lesson`.
Dars `GeneratedLesson` jadvalida suhbatga bog'lanib saqlanadi. Frontend sarlavha ostida qadamlar progressini ko'rsatadi.
Dars tugagach natija `AssessmentResult` (kind=lesson) ga yoziladi va `SubjectStats.sessions_completed` oshadi.
Keyingi darsda Ustoz kartadagi "keyingi qadam"dan davom ettiradi.

## API

| So'rov | Tavsif |
|---|---|
| `GET /api/v1/ai-teacher/chat/` | Suhbatlar ro'yxati |
| `POST /api/v1/ai-teacher/chat/` | Yangi suhbat: `{"subject_code_input": "english"}` |
| `GET /api/v1/ai-teacher/chat/{id}/` | Suhbat va uning xabarlari |
| `PATCH` / `DELETE /api/v1/ai-teacher/chat/{id}/` | Nomini o'zgartirish yoki o'chirish |
| `POST /api/v1/ai-teacher/chat/{id}/send/` | `{"message": "..."}`. Javob: xabar, `meta.tools_used` |
| `POST /api/v1/ai-teacher/chat/{id}/speak/` | multipart `audio`. Javob: xabarlar, `audio_base64` (mp3), `weak_words` |
| `GET /api/v1/ai-teacher/memory/` | Ustoz o'quvchi haqida eslab qolgan faktlar |
| `DELETE /api/v1/ai-teacher/memory/{id}/` | Bitta faktni o'chirish |
| `POST /api/v1/ai-teacher/memory/clear/` | Hammasini o'chirish |

## Admin panel

- **Support tickets**: AI Ustoz adminga uzatgan murojaatlar (to'lov, texnik nosozlik, shikoyat). Holatini ro'yxatdan turib o'zgartirish mumkin.
- **Assessment results**: daraja testi, test va speaking natijalari. Ular `kind` maydoni bilan ajratilgan.

## Qolgan TODO'lar

- `tools.py` → `escalate_to_admin`: adminga Telegram yoki email xabar yuborish
- `prompts.py` → `APP_FAQ`: ilovangizdagi aniq qadamlar
- Talaffuz bali faqat taxminiy. Aniq baholash uchun Azure Pronunciation Assessment kabi xizmat ulang
- `edge-tts` norasmiy xizmat. Pullik mahsulotda rasmiy Azure TTS ishonchliroq
