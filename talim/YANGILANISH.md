# Tezkor tuzatish: eski "Tinglang va o'qing" bo'limi olib tashlandi

"So'zlar" bo'limining "O'rganish" tabida eski, boshqa loyihadan qolgan "Tinglang va o'qing" kartasi bor edi
(`components/StoryLesson.jsx`). U mening ishim emas edi, lekin ko'rinib turgani uchun olib tashladim:

- Faqat 2 ta qattiq yozilgan matn bor edi, ikkalasi ham "A1" deb belgilangan.
- Tarjimani brauzerdan to'g'ridan-to'g'ri tashqi, kalitsiz ochiq API'larga (dictionaryapi.dev, mymemory.translated.net)
  murojaat qilib olardi — ular ko'pincha ishlamay, har bir so'z o'rniga "tarjima" degan placeholder matn chiqarardi
  (shuning uchun "bir xil so'z" ko'rinardi) va xato faqat brauzer konsoliga yozilib, ekranda umuman ko'rinmasdi.
- Bu hech qachon haqiqiy lug'at bazasidan foydalanmagan — shuning uchun "11 ta so'z, boshqasi yo'q" degan taassurot
  qoldirardi, aslida platforma lug'atida 9700+ so'z bor va bunga aloqasi yo'q edi.

Haqiqiy, backendga ulangan lug'at — yangi **Lug'at** bo'limi (`/app/dictionary`) — joyida qoldi, faqat endi
"So'zlar → O'rganish" sahifasida bitta, to'liq kengaytirilgan karta sifatida ko'rinadi.

## Google / Facebook hali ko'rinmasa

Kodda muammo topilmadi — sinovda ikkalasi ham kalit berilganda to'g'ri chiqadi. Agar sizda hali ko'rinmasa, tekshiring:

1. Kalitlar **backend/.env** faylida ekanligini (frontend/.env emas) va atrofida qo'shtirnoq yoki bo'sh joy yo'qligini.
2. `.env` ni o'zgartirgandan keyin backend serverni **qayta ishga tushirganingizni** (`runserver` yoki gunicorn/systemd
   qayta yuklanishi kerak — `.env` faqat server ishga tushganda o'qiladi).
3. Brauzeringizda tekshiring: `https://sizning-domen.uz/api/v1/auth/social/config/` manziliga kirsangiz,
   `google_client_id` va `facebook_app_id` qiymatlari bo'sh emasligini ko'rishingiz kerak. Bo'sh bo'lsa — muammo
   backend tomonida (.env/kalit). To'la bo'lsa-yu tugma baribir chiqmasa yoki "yuklab bo'lmadi" desa — bu odatda
   brauzerdagi AdBlock/uBlock kabi reklama blokerlari `accounts.google.com` yoki `connect.facebook.net` ni
   bloklaganidan bo'ladi; shu kengaytmalarni shu sayt uchun o'chirib ko'ring.

---

# Yangilanish (5-bosqich): so'zlar, lug'at, avatar, matematika, obuna, admin, Google/Facebook

## O'rnatish

```bash
cd backend
python manage.py migrate      # yangi: accounts 0003, session 0002, math_practice 0002-0003
cd ../frontend && npm install && npm run build
```

Obuna muddati tugaganda premiumni o'chirish uchun kuniga bir marta ishga tushiring (cron):

```
0 3 * * *  cd /srv/talim/backend && python manage.py expire_subscriptions
```

## Google va Facebook orqali kirish

Kalitlar faqat **backend/.env** ga yoziladi. Frontend ularni `GET /api/v1/auth/social/config/` orqali o'zi oladi.

```
GOOGLE_CLIENT_ID=1234567890-xxxx.apps.googleusercontent.com
FACEBOOK_APP_ID=1234567890
FACEBOOK_APP_SECRET=xxxxxxxx
FRONTEND_URL=https://sizning-domen.uz     # to'lovdan keyin qaytish manzili uchun
```

**Google:**
1. console.cloud.google.com → APIs & Services → Credentials.
2. Create credentials → OAuth client ID → Web application.
3. *Authorized JavaScript origins* ga quyidagilarni qo'shing:
   - `http://localhost:5173`
   - sayt domeni (`https://...`)
4. Redirect URI kerak emas.
5. Client ID ni `GOOGLE_CLIENT_ID` ga yozing.

**Facebook:**
1. developers.facebook.com → My Apps → Create App → "Authenticate and request data from users with Facebook Login".
2. Facebook Login → Settings bo'limida *Allowed Domains for the JavaScript SDK* ga domenni qo'shing.
3. App settings → Basic bo'limidan App ID va App Secret ni oling.
4. Ilova "Live" holatida bo'lishi kerak, aks holda faqat test foydalanuvchilar kira oladi.

Kalit yozilmagan tugma sahifada umuman ko'rinmaydi ("sozlanmagan" yozuvi endi chiqmaydi).

## Nima o'zgardi

| Bo'lim | O'zgarish |
|---|---|
| So'zlar | Vocabulary, Flashcard va So'z o'yini bitta "So'zlar" bo'limiga birlashtirildi: O'rganish, Takrorlash va O'yin tablari. Quiz alohida qoldi. Eski manzillar yangi bo'limga yo'naltiriladi |
| Lug'at | Yangi bo'lim. Inglizcha yoki o'zbekcha so'z bo'yicha qidiriladi. Har bir so'zda tarjima, misol, talaffuz va daraja bor, "O'rganishga qo'shish" tugmasi ham bor. Qidiruv bo'sh bo'lsa, kun so'zi ko'rsatiladi |
| Avatar suhbat | Yangi dizayn. Vaziyatlar: kafe, aeroport, mehmonxona, do'kon, ish suhbati, shifokor, IELTS. Amerika yoki Britaniya talaffuzini tanlash mumkin. Ovozli javob qaytadi. Xatolar suhbat ichida emas, alohida izohda ko'rsatiladi. Daraja o'quvchining o'zinikidan olinadi. Suhbat har kirishda yangidan boshlanmaydi. Premium avatar endi haqiqatan yopiq |
| Matematika | Javob tekshiruvi qayta yozildi: `x = 5`, `5`, `2,5`, `√2`, `π`, `5 sm`, bir nechta javob — hammasi to'g'ri tanib olinadi. Mavzular bo'yicha progress ko'rinadi. Maslahat, yechim va AI tushuntirishi bor. Isbot masalalarini o'quvchi o'zi tekshiradi. Ball faqat birinchi to'g'ri javob uchun beriladi |
| Obuna | Joriy tarif va qolgan kunlar ko'rsatiladi. Payme yoki Click tanlanadi. Qayta to'lov muddatni uzaytiradi. Muddat tugaganda premium o'chadi. To'lov bekor qilinsa premium qaytarib olinadi |
| Kirish va ro'yxatdan o'tish | Yangi dizayn. Email yoki login bilan kirish mumkin. Email tasdiqlanmagan bo'lsa, tasdiqlash sahifasiga yo'naltiradi |
| Admin | Yangi sahifalar: Statistika (haftalik grafik va tushum), Murojaatlar, Tariflar, Quizlar (e'lon qilish va AI bilan qayta tuzish). Foydalanuvchi qo'shilganda vaqtinchalik parol beriladi. Masalaga javob qo'shish mumkin. Video uchun YouTube havolasini qo'yish kifoya. Admin panelda endi ikkita menyu chiqmaydi |

## Topilgan va tuzatilgan xatolar

- Matematika: deyarli har bir to'g'ri javob "noto'g'ri" deb chiqardi. Bundan tashqari, o'quvchi javob yubora olmasdi (403 xatosi).
- To'lov: Payme yoki Click kaliti bo'lmasa, **production** da ham har kimga bepul premium berilardi. Endi bu sinov rejimi faqat `DEBUG=True` da ishlaydi.
- Premium hech qachon tugamasdi, qayta to'lov esa muddatni uzaytirmasdi.
- Google va Facebook: kirgandan keyin sahifa o'zgarmasdi. Bir xil username bo'lsa xato berardi. Facebook tokeni boshqa ilovaniki ekanligi tekshirilmasdi.
- Ro'yxatdan o'tishdagi "Ism" maydoni aslida login sifatida saqlanardi.
- Admin: flashcard qo'shishda fan `NaN` bo'lib ketardi. Admin qo'shgan foydalanuvchi tizimga kira olmasdi.

---

# Yangilanish: AI Ustoz, reja, dashboard, reyting, vocabulary, video, quiz, flashcard

## O'rnatish

```bash
cd backend
pip install -r requirements/base.txt
python manage.py migrate              # yangi migratsiyalar: ai_teacher 0002-0004, gamification 0002,
                                      # english_library 0004-0005, practice_tools 0002-0004, youtube 0002
python manage.py rebuild_quizzes      # eski "CEFR darajasini top" quizlarini haqiqiy savollarga aylantiradi
                                      # (grammatika quizlari uchun ANTHROPIC_API_KEY kerak)

cd ../frontend
npm install
npm run dev
```

`.env` faylida kerakli kalitlar:

```
ANTHROPIC_API_KEY=...     # AI Ustoz, tarjimalar, grammatika quizlari
YOUTUBE_API_KEY=...       # Video bo'limidagi qidiruv (kunlik limit: 10 000 birlik, 1 qidiruv ≈ 101 birlik)
```

Ovozli suhbat serverda ishlashi uchun (ixtiyoriy): `pip install -r requirements/speaking.txt`.
O'rnatilmasa, brauzerning o'z ovoz tanish funksiyasi ishlatiladi (Chrome va Edge'da ishlaydi, Firefox'da ishlamaydi).
AI Ustoz sahifasi qaysi qism sozlanmaganini o'zi ko'rsatadi (`GET /api/v1/ai-teacher/status/`).

## Nima o'zgardi

| Bo'lim | O'zgarish |
|---|---|
| O'quv reja | AI Ustoz kunlik, haftalik va oylik reja tuzadi. Reja Dashboard'da belgilanadi, mashq bajarilganda mos vazifa o'zi belgilanadi |
| Ovozli suhbat | Yangi rejim "Ustoz bilan suhbat": o'zbek, rus yoki ingliz tilida gapirish mumkin, til avtomatik aniqlanadi. Server ishlamasa brauzerga o'tadi, o'zbekcha ovoz bo'lmasa turkcha ovoz bilan o'qiydi |
| Dashboard | Haqiqiy ism, kunlik maqsad, haftalik grafik, reyting o'rni, o'quv reja, keyingi qadam, darajalar, natijalar |
| Ball va streak | Yagona tizim (`gamification/services.py`): quiz, flashcard, vocabulary, AI dars, reja, video, matematika. Streak endi haqiqatan hisoblanadi |
| Reyting | 1–50 o'rin: shu hafta, shu oy va barcha vaqt bo'yicha. Teng ball bo'lsa o'rin ham teng. O'quvchi top 50 da bo'lmasa, o'z o'rnini ko'radi |
| Vocabulary | Tarjima va misollar (flashcardlardan va AI orqali, bir marta to'ldiriladi). Kunlik 10 so'z: tanishuv, keyin mashq. "Bilaman" tugmasi. Barcha so'zlar ro'yxati qidiruv bilan. Darajalar qulflanmaydi |
| Video | YouTube qidiruvi va platformaning o'zida ko'rish. Darajaga mos tavsiya so'rovlari. Natija 6 soat keshlanadi. Kalit yoki limit bo'lmasa, bazadagi videolar ichidan qidiradi |
| Quiz | Daraja bo'yicha tartiblangan. Bitta-bitta savol beriladi va javob darhol ko'rsatiladi. Eng yaxshi natija saqlanadi. Ball faqat natija yaxshilansa beriladi |
| Flashcard | Kunlik sessiya (5, 10 yoki 20 ta yangi karta va takrorlash vaqti kelganlar). "Yodlash" va "Yozish" rejimlari, yo'nalish tanlash, 4 xil baho |
| Mobil | Chap menyu mobil ekranda yuqoridagi gorizontal qatorga aylanadi |
