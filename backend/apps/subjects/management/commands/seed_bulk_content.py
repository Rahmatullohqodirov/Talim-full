"""Platformani ishga tushirish uchun yetarli miqdorda mashq kontenti qo'shadi.

Muammo: boshlang'ich seed_initial_data faqat 3-5 tadan demo yozuv qo'shar edi —
shu sababli Flashcard bo'limi "5 tadan keyin tugab qolyapti" kabi ko'rinardi
(aslida bug emas, shunchaki bazada 5 tadan ortiq karta yo'q edi).

Bu buyruq xavfsiz (idempotent): qayta ishga tushirilsa ham dublikat yaratmaydi
(get_or_create orqali), shuning uchun uni istalgan vaqt qayta ishga tushirish mumkin:

    python manage.py seed_bulk_content
"""
from django.core.management.base import BaseCommand

from apps.subjects.models import Subject
from apps.practice_tools.models import Flashcard, Quiz, QuizQuestion
from apps.math_practice.models import MathTopic, MathProblem


FLASHCARDS = [
    # --- Olmoshlar / asosiy so'zlar ---
    ("I", "men"), ("you", "sen / siz"), ("he", "u (erkak)"), ("she", "u (ayol)"),
    ("it", "u (jonsiz)"), ("we", "biz"), ("they", "ular"), ("this", "bu"), ("that", "u/o'sha"),
    ("these", "bular"), ("those", "ular/o'shalar"),
    # --- Fe'llar ---
    ("read", "o'qimoq"), ("write", "yozmoq"), ("break", "sindirmoq"), ("eat", "yemoq"),
    ("drink", "ichmoq"), ("leave", "ketmoq, qoldirmoq"), ("meet", "uchratmoq"),
    ("hold", "ushlamoq"), ("close", "yopmoq"), ("open", "ochmoq"), ("hear", "eshitmoq"),
    ("listen", "tinglamoq"), ("speak", "gapirmoq"), ("say", "aytmoq"), ("tell", "aytib bermoq"),
    ("ask", "so'ramoq"), ("answer", "javob bermoq"), ("understand", "tushunmoq"),
    ("know", "bilmoq"), ("think", "o'ylamoq"), ("believe", "ishonmoq"), ("want", "xohlamoq"),
    ("need", "kerak bo'lmoq"), ("like", "yoqtirmoq"), ("love", "sevmoq"), ("hate", "yomon ko'rmoq"),
    ("work", "ishlamoq"), ("study", "o'qimoq (ta'lim)"), ("learn", "o'rganmoq"),
    ("teach", "o'rgatmoq"), ("play", "o'ynamoq"), ("run", "yugurmoq"), ("walk", "yurmoq"),
    ("sit", "o'tirmoq"), ("stand", "turmoq"), ("sleep", "uxlamoq"), ("wake up", "uyg'onmoq"),
    ("cook", "pishirmoq"), ("clean", "tozalamoq"), ("wash", "yuvmoq"), ("buy", "sotib olmoq"),
    ("sell", "sotmoq"), ("pay", "to'lamoq"), ("spend", "sarflamoq"), ("save", "tejamoq"),
    ("send", "yubormoq"), ("receive", "qabul qilmoq"), ("bring", "olib kelmoq"),
    ("take", "olmoq"), ("give", "bermoq"), ("show", "ko'rsatmoq"), ("find", "topmoq"),
    ("lose", "yo'qotmoq"), ("look for", "qidirmoq"), ("wait", "kutmoq"), ("start", "boshlamoq"),
    ("finish", "tugatmoq"), ("stop", "to'xtatmoq"), ("continue", "davom ettirmoq"),
    ("help", "yordam bermoq"), ("try", "harakat qilmoq"), ("decide", "qaror qilmoq"),
    ("forget", "unutmoq"), ("remember", "eslamoq"), ("change", "o'zgartirmoq"),
    ("grow", "o'smoq"), ("build", "qurmoq"), ("travel", "sayohat qilmoq"), ("arrive", "yetib kelmoq"),
    ("leave for", "jo'namoq"), ("visit", "tashrif buyurmoq"), ("live", "yashamoq"),
    ("die", "vafot etmoq"), ("marry", "turmush qurmoq"), ("borrow", "qarz olmoq"),
    ("lend", "qarz bermoq"), ("smile", "tabassum qilmoq"), ("laugh", "kulmoq"), ("cry", "yig'lamoq"),
    ("shout", "baqirmoq"), ("whisper", "shivirlamoq"), ("push", "itarmoq"), ("pull", "tortmoq"),
    ("carry", "ko'tarib yurmoq"), ("drop", "tushirib yubormoq"), ("catch", "ushlab olmoq"),
    ("throw", "otmoq"), ("fix", "tuzatmoq"), ("break down", "buzilib qolmoq"), ("turn on", "yoqmoq"),
    ("turn off", "o'chirmoq"),
    # --- Sifatlar ---
    ("big", "katta"), ("small", "kichik"), ("tall", "baland (bo'y)"), ("short", "past/qisqa"),
    ("long", "uzun"), ("fast", "tez"), ("slow", "sekin"), ("happy", "baxtli"),
    ("sad", "xafa"), ("angry", "jahldor"), ("tired", "charchagan"), ("hungry", "och"),
    ("thirsty", "chanqagan"), ("strong", "kuchli"), ("weak", "kuchsiz"), ("beautiful", "chiroyli"),
    ("ugly", "xunuk"), ("clean", "toza"), ("dirty", "iflos"), ("easy", "oson"),
    ("difficult", "qiyin"), ("cheap", "arzon"), ("expensive", "qimmat"), ("new", "yangi"),
    ("old", "eski/keksa"), ("young", "yosh"), ("rich", "boy"), ("poor", "kambag'al"),
    ("hot", "issiq"), ("cold", "sovuq"), ("warm", "iliq"), ("bright", "yorug'"),
    ("dark", "qorong'i"), ("quiet", "jim/osoyishta"), ("loud", "baland ovozli"),
    ("healthy", "sog'lom"), ("sick", "kasal"), ("safe", "xavfsiz"), ("dangerous", "xavfli"),
    ("important", "muhim"), ("necessary", "zarur"), ("possible", "mumkin"), ("famous", "mashhur"),
    # --- Vaqt / kunlar ---
    ("today", "bugun"), ("tomorrow", "ertaga"), ("yesterday", "kecha"), ("morning", "ertalab"),
    ("afternoon", "tushdan keyin"), ("evening", "kechqurun"), ("night", "tun"),
    ("week", "hafta"), ("month", "oy"), ("year", "yil"), ("always", "doim"),
    ("never", "hech qachon"), ("sometimes", "ba'zan"), ("often", "tez-tez"), ("usually", "odatda"),
    # --- Oila / odamlar ---
    ("family", "oila"), ("mother", "ona"), ("father", "ota"), ("brother", "aka/uka"),
    ("sister", "opa/singil"), ("friend", "do'st"), ("neighbor", "qo'shni"), ("teacher", "o'qituvchi"),
    ("student", "talaba/o'quvchi"), ("doctor", "shifokor"),
    # --- Ovqat / uy ---
    ("food", "ovqat"), ("water", "suv"), ("bread", "non"), ("meat", "go'sht"),
    ("vegetable", "sabzavot"), ("fruit", "meva"), ("house", "uy"), ("room", "xona"),
    ("kitchen", "oshxona"), ("door", "eshik"), ("window", "deraza"), ("table", "stol"),
    ("chair", "stul"), ("bed", "krovat"),
]

QUIZZES = [
    {
        "title": "Present Simple — 1-daraja",
        "questions": [
            ("She ___ to school every day.", ["go", "goes", "going", "went"], 1),
            ("They ___ football on weekends.", ["plays", "playing", "play", "played"], 2),
            ("I ___ coffee every morning.", ["drink", "drinks", "drinking", "drank"], 0),
            ("He ___ in a bank.", ["work", "working", "works", "worked"], 2),
            ("We ___ English at school.", ["study", "studies", "studying", "studied"], 0),
            ("My sister ___ TV in the evening.", ["watch", "watches", "watching", "watched"], 1),
            ("The shop ___ at 9 pm.", ["close", "closing", "closes", "closed"], 2),
            ("Dogs ___ loudly.", ["bark", "barks", "barking", "barked"], 0),
        ],
    },
    {
        "title": "Past Simple — 1-daraja",
        "questions": [
            ("I ___ to the cinema yesterday.", ["go", "went", "gone", "goes"], 1),
            ("She ___ a letter last night.", ["write", "wrote", "writes", "writing"], 1),
            ("They ___ dinner at 7 pm.", ["eat", "ate", "eaten", "eating"], 1),
            ("We ___ football last weekend.", ["play", "played", "plays", "playing"], 1),
            ("He ___ his keys yesterday.", ["lose", "lost", "loses", "losing"], 1),
            ("I ___ very tired after work.", ["was", "were", "is", "am"], 0),
        ],
    },
    {
        "title": "Sifatlar va taqqoslash",
        "questions": [
            ("This book is ___ than that one.", ["interesting", "more interesting", "most interesting", "interestinger"], 1),
            ("He is the ___ student in the class.", ["good", "better", "best", "well"], 2),
            ("My car is ___ than yours.", ["fast", "faster", "fastest", "more fast"], 1),
            ("This is the ___ day of my life.", ["happy", "happier", "happiest", "more happy"], 2),
            ("She is ___ than her brother.", ["tall", "taller", "tallest", "more tall"], 1),
        ],
    },
    {
        "title": "Predloglar (Prepositions)",
        "questions": [
            ("The book is ___ the table.", ["in", "on", "at", "under"], 1),
            ("We arrived ___ 8 o'clock.", ["in", "on", "at", "by"], 2),
            ("She lives ___ Tashkent.", ["in", "on", "at", "to"], 0),
            ("He is good ___ math.", ["in", "on", "at", "for"], 2),
            ("I'm waiting ___ the bus.", ["for", "to", "at", "on"], 0),
        ],
    },
    {
        "title": "Kundalik so'zlashuv",
        "questions": [
            ("How ___ you?", ["is", "am", "are", "be"], 2),
            ("Nice to ___ you!", ["meet", "meets", "meeting", "met"], 0),
            ("What time ___ it?", ["is", "are", "am", "be"], 0),
            ("Can you ___ me, please?", ["help", "helps", "helping", "helped"], 0),
            ("Where ___ you from?", ["is", "am", "are", "be"], 2),
        ],
    },
]

MATH_TOPICS = {
    "Algebra": [
        ("2x + 5 = 15. x ni toping.", 1, ["2x = 10", "x = 5"]),
        ("3x - 7 = 8. x ni toping.", 1, ["3x = 15", "x = 5"]),
        ("5(x + 2) = 25. x ni toping.", 2, ["x + 2 = 5", "x = 3"]),
        ("2x + 3y = 12, x = 3 bo'lsa, y ni toping.", 2, ["6 + 3y = 12", "3y = 6", "y = 2"]),
        ("x/4 + 3 = 7. x ni toping.", 1, ["x/4 = 4", "x = 16"]),
    ],
    "Geometriya": [
        ("Tomoni 4 sm bo'lgan kvadratning yuzini toping.", 1, ["S = a^2 = 16 sm^2"]),
        ("Uzunligi 6 sm, kengligi 3 sm bo'lgan to'g'ri to'rtburchakning perimetrini toping.", 1, ["P = 2(a+b) = 2(6+3) = 18 sm"]),
        ("Radiusi 5 sm bo'lgan doiraning yuzini toping (pi=3.14).", 2, ["S = pi*r^2 = 3.14*25 = 78.5 sm^2"]),
        ("Tomonlari 3, 4, 5 sm bo'lgan uchburchak to'g'ri burchakli ekanini isbotlang.", 2, ["3^2+4^2=9+16=25=5^2", "Pifagor teoremasiga ko'ra to'g'ri burchakli"]),
        ("Balandligi 6 sm, asosi 8 sm bo'lgan uchburchakning yuzini toping.", 1, ["S = (a*h)/2 = (8*6)/2 = 24 sm^2"]),
    ],
    "Funksiyalar": [
        ("f(x) = x^2 - 4. f(3) ni toping.", 2, ["f(3) = 9 - 4 = 5"]),
        ("f(x) = 2x + 1. f(0) va f(5) ni toping.", 1, ["f(0) = 1", "f(5) = 11"]),
        ("f(x) = x^2. f(x) ning eng kichik qiymatini toping.", 2, ["Minimal qiymat x=0 da, f(0)=0"]),
        ("f(x) = 3x - 2 funksiyaning x-o'qi bilan kesishish nuqtasini toping.", 2, ["3x - 2 = 0", "x = 2/3"]),
    ],
    "Tenglamalar": [
        ("x^2 - 5x + 6 = 0 tenglamani yeching.", 3, ["(x-2)(x-3) = 0", "x = 2 yoki x = 3"]),
        ("x^2 - 9 = 0 tenglamani yeching.", 2, ["x^2 = 9", "x = 3 yoki x = -3"]),
        ("2x^2 - 8x = 0 tenglamani yeching.", 2, ["2x(x-4) = 0", "x = 0 yoki x = 4"]),
        ("x^2 + 2x + 1 = 0 tenglamani yeching.", 3, ["(x+1)^2 = 0", "x = -1"]),
    ],
    "Statistika": [
        ("2, 4, 4, 6, 8 sonlarining o'rtacha arifmetigini toping.", 1, ["(2+4+4+6+8)/5 = 24/5 = 4.8"]),
        ("1, 3, 3, 5, 7, 9 sonlarining medianasini toping.", 2, ["Tartiblangan qator o'rtasidagi 3 va 5 ning o'rtachasi = 4"]),
        ("5, 7, 7, 9 sonlarining modasini toping.", 1, ["Eng ko'p takrorlangan son: 7"]),
    ],
    "Foizlar": [
        ("120 ning 25% ini toping.", 1, ["120 * 0.25 = 30"]),
        ("Narxi 80000 so'm bo'lgan mahsulot 15% chegirma bilan sotilmoqda. Yangi narxni toping.", 2, ["Chegirma = 80000*0.15=12000", "Yangi narx = 80000-12000=68000 so'm"]),
        ("40 ning necha foizi 10 ga teng?", 2, ["10/40 * 100 = 25%"]),
    ],
}


class Command(BaseCommand):
    help = "Flashcard, Quiz va MathProblem bo'limlariga yetarli miqdorda kontent qo'shadi (idempotent)."

    def handle(self, *args, **options):
        english = Subject.objects.filter(code="english").first()
        if not english:
            self.stdout.write(self.style.ERROR(
                "'english' fani topilmadi — avval `python manage.py seed_initial_data` ni ishga tushiring."
            ))
            return

        created_flashcards = 0
        for front, back in FLASHCARDS:
            _, created = Flashcard.objects.get_or_create(
                subject=english, front_text=front, defaults={"back_text": back}
            )
            if created:
                created_flashcards += 1
        self.stdout.write(self.style.SUCCESS(
            f"Flashcard: {created_flashcards} ta yangi qo'shildi (jami {Flashcard.objects.filter(subject=english).count()} ta)."
        ))

        created_questions = 0
        for quiz_data in QUIZZES:
            quiz, _ = Quiz.objects.get_or_create(subject=english, title=quiz_data["title"])
            for text, choices, correct_index in quiz_data["questions"]:
                _, created = QuizQuestion.objects.get_or_create(
                    quiz=quiz, text=text,
                    defaults={"choices": choices, "correct_index": correct_index},
                )
                if created:
                    created_questions += 1
        self.stdout.write(self.style.SUCCESS(f"QuizQuestion: {created_questions} ta yangi qo'shildi."))

        created_problems = 0
        for topic_name, problems in MATH_TOPICS.items():
            topic, _ = MathTopic.objects.get_or_create(name=topic_name)
            for statement, difficulty, steps in problems:
                _, created = MathProblem.objects.get_or_create(
                    topic=topic, statement=statement,
                    defaults={"difficulty": difficulty, "solution_steps": steps},
                )
                if created:
                    created_problems += 1
        self.stdout.write(self.style.SUCCESS(f"MathProblem: {created_problems} ta yangi qo'shildi."))

        self.stdout.write(self.style.SUCCESS(
            "Tayyor! Endi Flashcard/Quiz/Math bo'limlari 5 tadan keyin tugamaydi."
        ))
