"""Boshlang'ich (A1) darslar va hikoyalarni tayyor, qo'lda yozilgan kontent bilan to'ldiradi — ANTHROPIC_API_KEY
kerak emas. Keyinroq ko'proq dars/hikoya qo'shish uchun `generate_lessons` (AI) yoki admin panel ishlatiladi.

    python manage.py seed_lessons_stories
"""
from django.core.management.base import BaseCommand
from django.db import transaction


LESSONS = [
    {
        "title": "Fe'lning asosiy shakli (to be)",
        "explanation": (
            "\"To be\" fe'li inglizcha gaplarning asosi: am/is/are. Men uchun — am (I am), u/bu uchun — is "
            "(he/she/it is), biz/siz/ular uchun — are (we/you/they are). Masalan: I am a student. She is happy."
        ),
        "words": [
            ("am", "-man (I bilan)"), ("is", "-dir (he/she/it bilan)"), ("are", "-siz/-lar (we/you/they bilan)"),
            ("student", "o'quvchi, talaba"), ("happy", "baxtli"), ("teacher", "o'qituvchi"),
            ("doctor", "shifokor"), ("tired", "charchagan"),
        ],
        "exercises": [
            ("en_uz", "am", "-man (I bilan)"), ("en_uz", "is", "-dir (he/she/it bilan)"),
            ("en_uz", "student", "o'quvchi, talaba"), ("en_uz", "happy", "baxtli"),
            ("uz_en", "-siz/-lar (we/you/they bilan)", "are"), ("uz_en", "o'qituvchi", "teacher"),
            ("uz_en", "shifokor", "doctor"), ("uz_en", "charchagan", "tired"),
            ("fill_blank", "I ___ a student.", "am", ["am", "is", "are", "be"]),
            ("fill_blank", "She ___ a doctor.", "is", ["am", "is", "are", "be"]),
            ("fill_blank", "They ___ happy.", "are", ["am", "is", "are", "be"]),
            ("build_sentence", "happy / is / He", "He is happy", ["He", "is", "happy"]),
        ],
    },
    {
        "title": "So'roq so'zlar (what, where, who)",
        "explanation": (
            "Savol so'zlari gapni savolga aylantiradi: what (nima), where (qayerda), who (kim), "
            "when (qachon), why (nega), how (qanday). Masalan: What is your name? Where do you live?"
        ),
        "words": [
            ("what", "nima"), ("where", "qayerda"), ("who", "kim"), ("when", "qachon"),
            ("why", "nega"), ("how", "qanday"), ("name", "ism"), ("live", "yashamoq"),
        ],
        "exercises": [
            ("en_uz", "what", "nima"), ("en_uz", "where", "qayerda"), ("en_uz", "who", "kim"), ("en_uz", "when", "qachon"),
            ("uz_en", "nega", "why"), ("uz_en", "qanday", "how"), ("uz_en", "ism", "name"), ("uz_en", "yashamoq", "live"),
            ("fill_blank", "___ is your name?", "What", ["What", "Where", "Who", "When"]),
            ("fill_blank", "___ do you live?", "Where", ["What", "Where", "Who", "When"]),
            ("fill_blank", "___ is that boy?", "Who", ["What", "Where", "Who", "When"]),
            ("build_sentence", "your / is / name / What", "What is your name", ["What", "is", "your", "name"]),
        ],
    },
    {
        "title": "Olmoshlar (I, you, he, she)",
        "explanation": (
            "Shaxs olmoshlari: I (men), you (sen/siz), he (u-erkak), she (u-ayol), it (u-narsa/hayvon), "
            "we (biz), they (ular). Gapda ism o'rniga ishlatiladi: Aziz is tired -> He is tired."
        ),
        "words": [
            ("I", "men"), ("you", "sen, siz"), ("he", "u (erkak)"), ("she", "u (ayol)"),
            ("it", "u (narsa)"), ("we", "biz"), ("they", "ular"),
        ],
        "exercises": [
            ("en_uz", "he", "u (erkak)"), ("en_uz", "she", "u (ayol)"), ("en_uz", "we", "biz"), ("en_uz", "they", "ular"),
            ("uz_en", "men", "I"), ("uz_en", "sen, siz", "you"), ("uz_en", "u (narsa)", "it"),
            ("fill_blank", "___ am a student. (men)", "I", ["I", "He", "She", "It"]),
            ("fill_blank", "Aziz is tired. ___ is tired.", "He", ["I", "He", "She", "It"]),
            ("build_sentence", "happy / are / We", "We are happy", ["We", "are", "happy"]),
        ],
    },
    {
        "title": "Egalik olmoshlari (my, your, his)",
        "explanation": (
            "Egalik olmoshlari kimgadir tegishli narsani bildiradi: my (mening), your (sening/sizning), "
            "his (uning-erkak), her (uning-ayol), our (bizning), their (ularning)."
        ),
        "words": [
            ("my", "mening"), ("your", "sening, sizning"), ("his", "uning (erkak)"), ("her", "uning (ayol)"),
            ("our", "bizning"), ("their", "ularning"), ("book", "kitob"), ("house", "uy"),
        ],
        "exercises": [
            ("en_uz", "my", "mening"), ("en_uz", "his", "uning (erkak)"), ("en_uz", "her", "uning (ayol)"), ("en_uz", "book", "kitob"),
            ("uz_en", "bizning", "our"), ("uz_en", "ularning", "their"), ("uz_en", "uy", "house"),
            ("fill_blank", "This is ___ book. (mening)", "my", ["my", "your", "his", "her"]),
            ("fill_blank", "That is ___ house. (uning-ayol)", "her", ["my", "your", "his", "her"]),
            ("build_sentence", "book / my / is / This", "This is my book", ["This", "is", "my", "book"]),
        ],
    },
    {
        "title": "Ko'plik son (plural nouns)",
        "explanation": (
            "Ko'pchilik otlarga -s qo'shiladi: book -> books, cat -> cats. -s, -x, -ch, -sh bilan tugasa -es "
            "qo'shiladi: box -> boxes. Ba'zilari istisno: child -> children, man -> men."
        ),
        "words": [
            ("books", "kitoblar"), ("cats", "mushuklar"), ("boxes", "qutilar"), ("children", "bolalar"),
            ("men", "erkaklar"), ("women", "ayollar"), ("pens", "ruchkalar"),
        ],
        "exercises": [
            ("en_uz", "books", "kitoblar"), ("en_uz", "children", "bolalar"), ("en_uz", "men", "erkaklar"),
            ("uz_en", "mushuklar", "cats"), ("uz_en", "qutilar", "boxes"), ("uz_en", "ayollar", "women"),
            ("fill_blank", "I have two ___. (cat)", "cats", ["cat", "cats", "cates", "catss"]),
            ("fill_blank", "Three ___ are playing. (child)", "children", ["childs", "children", "childes", "child"]),
            ("build_sentence", "two / have / I / boxes", "I have two boxes", ["I", "have", "two", "boxes"]),
        ],
    },
    {
        "title": "Ko'rsatkich so'zlar (this, that, these, those)",
        "explanation": (
            "This (bu, yaqin, bitta) / these (bular, yaqin, ko'p) / that (u/ana, uzoq, bitta) / "
            "those (ular/anavi, uzoq, ko'p). Masalan: This is my pen. Those are your books."
        ),
        "words": [
            ("this", "bu"), ("that", "u, ana u"), ("these", "bular"), ("those", "ular, anavilar"),
            ("pen", "ruchka"), ("near", "yaqin"), ("far", "uzoq"),
        ],
        "exercises": [
            ("en_uz", "this", "bu"), ("en_uz", "that", "u, ana u"), ("en_uz", "these", "bular"), ("en_uz", "those", "ular, anavilar"),
            ("uz_en", "ruchka", "pen"), ("uz_en", "yaqin", "near"), ("uz_en", "uzoq", "far"),
            ("fill_blank", "___ is my pen. (yaqin, bitta)", "This", ["This", "That", "These", "Those"]),
            ("fill_blank", "___ are your books. (uzoq, ko'p)", "Those", ["This", "That", "These", "Those"]),
            ("build_sentence", "pen / my / is / This", "This is my pen", ["This", "is", "my", "pen"]),
        ],
    },
    {
        "title": "Old ko'makchilar (in, on, at)",
        "explanation": (
            "In — ichida (in the box), on — ustida (on the table), at — aniq nuqtada/vaqtda "
            "(at school, at 5 o'clock). Joy va vaqtni bildirishda muhim."
        ),
        "words": [
            ("in", "ichida"), ("on", "ustida"), ("at", "da (aniq joy/vaqt)"), ("table", "stol"),
            ("box", "quti"), ("school", "maktab"), ("home", "uy"),
        ],
        "exercises": [
            ("en_uz", "in", "ichida"), ("en_uz", "on", "ustida"), ("en_uz", "at", "da (aniq joy/vaqt)"),
            ("uz_en", "stol", "table"), ("uz_en", "quti", "box"), ("uz_en", "maktab", "school"),
            ("fill_blank", "The book is ___ the table.", "on", ["in", "on", "at", "to"]),
            ("fill_blank", "I am ___ school.", "at", ["in", "on", "at", "to"]),
            ("fill_blank", "The pen is ___ the box.", "in", ["in", "on", "at", "to"]),
            ("build_sentence", "table / the / on / is / book / The", "The book is on the table",
             ["The", "book", "is", "on", "the", "table"]),
        ],
    },
    {
        "title": "There is / There are",
        "explanation": (
            "\"There is\" — bitta narsa bor (there is a cat), \"there are\" — bir nechta narsa bor "
            "(there are two cats). Biror narsaning mavjudligini aytish uchun ishlatiladi."
        ),
        "words": [
            ("there is", "bor (bitta)"), ("there are", "bor (ko'p)"), ("a cat", "mushuk"),
            ("some", "bir nechta"), ("many", "ko'p"), ("room", "xona"),
        ],
        "exercises": [
            ("en_uz", "there is", "bor (bitta)"), ("en_uz", "there are", "bor (ko'p)"), ("en_uz", "room", "xona"),
            ("uz_en", "bir nechta", "some"), ("uz_en", "ko'p", "many"),
            ("fill_blank", "___ a cat in the room.", "There is", ["There is", "There are", "Is there", "Are there"]),
            ("fill_blank", "___ two books on the table.", "There are", ["There is", "There are", "Is there", "Are there"]),
            ("build_sentence", "cat / is / a / room / the / in / There", "There is a cat in the room",
             ["There", "is", "a", "cat", "in", "the", "room"]),
        ],
    },
    {
        "title": "Present Simple",
        "explanation": (
            "Odatiy/doimiy ish-harakatlar uchun: I/you/we/they + fe'l (I play), he/she/it + fe'l+s "
            "(he plays). Masalan: I go to school every day. She reads books."
        ),
        "words": [
            ("play", "o'ynamoq"), ("plays", "o'ynaydi (he/she/it)"), ("go", "bormoq"),
            ("goes", "boradi (he/she/it)"), ("read", "o'qimoq"), ("every day", "har kuni"),
        ],
        "exercises": [
            ("en_uz", "play", "o'ynamoq"), ("en_uz", "goes", "boradi (he/she/it)"), ("en_uz", "every day", "har kuni"),
            ("uz_en", "bormoq", "go"), ("uz_en", "o'qimoq", "read"), ("uz_en", "o'ynaydi (he/she/it)", "plays"),
            ("fill_blank", "I ___ to school every day.", "go", ["go", "goes", "going", "went"]),
            ("fill_blank", "She ___ books.", "reads", ["read", "reads", "reading", "readed"]),
            ("build_sentence", "football / plays / He / every day", "He plays football every day",
             ["He", "plays", "football", "every", "day"]),
        ],
    },
    {
        "title": "Sonlar va vaqt",
        "explanation": (
            "Sonlar: one, two, three... ten. Soat so'rash: What time is it? — It's five o'clock. "
            "Kun, hafta, oy nomlarini bilish ham shu mavzuga kiradi."
        ),
        "words": [
            ("one", "bir"), ("five", "besh"), ("ten", "o'n"), ("o'clock", "soat (aniq)"),
            ("Monday", "dushanba"), ("today", "bugun"), ("tomorrow", "ertaga"),
        ],
        "exercises": [
            ("en_uz", "five", "besh"), ("en_uz", "o'clock", "soat (aniq)"), ("en_uz", "Monday", "dushanba"),
            ("uz_en", "bir", "one"), ("uz_en", "o'n", "ten"), ("uz_en", "bugun", "today"), ("uz_en", "ertaga", "tomorrow"),
            ("fill_blank", "It is five ___.", "o'clock", ["o'clock", "hour", "time", "clock"]),
            ("fill_blank", "Today is ___. (dushanba)", "Monday", ["Monday", "Tuesday", "today", "tomorrow"]),
            ("build_sentence", "it / time / is / What", "What time is it", ["What", "time", "is", "it"]),
        ],
    },
]

STORIES = [
    {
        "title": "My Day", "emoji": "🌅",
        "text": (
            "I wake up at seven o'clock. First, I wash my face. Then I get dressed and eat breakfast. "
            "I walk to school with my friend. I like my school. After school, I do my homework and play "
            "outside. In the evening, I eat dinner with my family. Then I read a book. I go to bed at nine o'clock."
        ),
        "questions": [
            ("What time do I wake up?", ["Six o'clock", "Seven o'clock", "Eight o'clock", "Nine o'clock"], "Seven o'clock"),
            ("Who do I walk to school with?", ["My brother", "My teacher", "My friend", "Alone"], "My friend"),
            ("What do I do after school?", ["Sleep", "Go shopping", "Homework and play", "Watch TV"], "Homework and play"),
            ("When do I eat dinner?", ["Morning", "Afternoon", "Evening", "Night"], "Evening"),
            ("What time do I go to bed?", ["Seven", "Eight", "Nine", "Ten"], "Nine"),
        ],
    },
    {
        "title": "My Family", "emoji": "👨‍👩‍👧",
        "text": (
            "My name is Malika. I have a big family. My father is a doctor. My mother is a teacher. "
            "I have one brother and one sister. My brother is ten years old. My sister is five years old. "
            "We live in a nice house. On weekends, we cook together and play games. I love my family."
        ),
        "questions": [
            ("What is my father's job?", ["Teacher", "Doctor", "Driver", "Engineer"], "Doctor"),
            ("What is my mother's job?", ["Doctor", "Nurse", "Teacher", "Cook"], "Teacher"),
            ("How old is my brother?", ["Five", "Seven", "Ten", "Twelve"], "Ten"),
            ("How old is my sister?", ["Three", "Five", "Eight", "Ten"], "Five"),
            ("What do we do on weekends?", ["Nothing", "Work", "Cook and play games", "Sleep all day"], "Cook and play games"),
        ],
    },
    {
        "title": "My Home", "emoji": "🏠",
        "text": (
            "I live in a small house with my family. My house has three rooms: a bedroom, a kitchen, and "
            "a living room. My bedroom is small but cozy. There is a bed, a table, and a chair. The kitchen "
            "is where my mother cooks delicious food. In the living room, we watch TV together in the evening. "
            "I love my home."
        ),
        "questions": [
            ("How many rooms does my house have?", ["Two", "Three", "Four", "Five"], "Three"),
            ("What is in my bedroom?", ["A sofa", "A bed, table and chair", "A TV", "Nothing"], "A bed, table and chair"),
            ("Who cooks in the kitchen?", ["My father", "My mother", "My sister", "I"], "My mother"),
            ("Where do we watch TV?", ["Bedroom", "Kitchen", "Living room", "Outside"], "Living room"),
            ("How does the author feel about home?", ["Loves it", "Hates it", "Doesn't care", "Is bored"], "Loves it"),
        ],
    },
    {
        "title": "At School", "emoji": "🏫",
        "text": (
            "I go to school every day except Sunday. My favourite subject is English. My teacher's name "
            "is Mr. Aziz. He is very kind. We have five lessons every day. At break time, I play with my "
            "friends in the yard. After lessons, I go home and have lunch. I like my school very much."
        ),
        "questions": [
            ("Which day don't I go to school?", ["Saturday", "Sunday", "Monday", "Friday"], "Sunday"),
            ("What is my favourite subject?", ["Math", "Science", "English", "Art"], "English"),
            ("What is my teacher's name?", ["Mr. Aziz", "Mr. John", "Mrs. Malika", "Mr. Sardor"], "Mr. Aziz"),
            ("How many lessons do we have every day?", ["Three", "Four", "Five", "Six"], "Five"),
            ("What do I do at break time?", ["Study", "Sleep", "Play with friends", "Eat lunch"], "Play with friends"),
        ],
    },
    {
        "title": "Food I Like", "emoji": "🍲",
        "text": (
            "I like many kinds of food. For breakfast, I eat bread and eggs with tea. For lunch, I often "
            "eat soup or rice with meat. My favourite food is plov. My mother cooks it every Sunday. "
            "For dinner, I eat something light, like salad or soup. I drink a lot of water every day."
        ),
        "questions": [
            ("What do I eat for breakfast?", ["Rice", "Bread and eggs", "Soup", "Plov"], "Bread and eggs"),
            ("What do I often eat for lunch?", ["Cake", "Soup or rice with meat", "Fruit", "Bread only"], "Soup or rice with meat"),
            ("What is my favourite food?", ["Soup", "Salad", "Plov", "Bread"], "Plov"),
            ("When does my mother cook plov?", ["Every day", "Every Sunday", "Every Monday", "Never"], "Every Sunday"),
            ("What do I drink a lot of?", ["Tea", "Juice", "Water", "Milk"], "Water"),
        ],
    },
    {
        "title": "Our Vacation", "emoji": "🏖️",
        "text": (
            "Last summer, my family went on vacation to the seaside. We travelled by car for five hours. "
            "The weather was sunny and warm. We swam in the sea every day and built sandcastles. In the "
            "evening, we ate fish and watched the sunset. It was the best vacation of my life."
        ),
        "questions": [
            ("Where did we go on vacation?", ["Mountains", "Seaside", "City", "Forest"], "Seaside"),
            ("How did we travel?", ["By plane", "By train", "By car", "By bus"], "By car"),
            ("What was the weather like?", ["Cold", "Rainy", "Sunny and warm", "Snowy"], "Sunny and warm"),
            ("What did we do every day?", ["Read books", "Swam in the sea", "Shopped", "Studied"], "Swam in the sea"),
            ("What did we eat in the evening?", ["Meat", "Fish", "Soup", "Bread"], "Fish"),
        ],
    },
]


class Command(BaseCommand):
    help = "A1 darslar va hikoyalarni tayyor (AI kerak bo'lmagan) kontent bilan to'ldiradi"

    def handle(self, *args, **opts):
        from apps.subjects.models import CEFRLevel, Subject
        from apps.lessons.models import Lesson, LessonExercise, LessonWord, Story, StoryQuestion

        subject = Subject.objects.filter(code="english").first()
        level = CEFRLevel.objects.filter(subject=subject, code="A1").first() if subject else None
        if not subject or not level:
            self.stderr.write(self.style.ERROR("english/A1 topilmadi — avval seed_initial_data ishga tushiring."))
            return

        with transaction.atomic():
            l_created = 0
            for i, l in enumerate(LESSONS):
                if Lesson.objects.filter(subject=subject, cefr_level=level, title=l["title"]).exists():
                    continue
                lesson = Lesson.objects.create(
                    subject=subject, cefr_level=level, order=i, title=l["title"],
                    explanation=l["explanation"], is_published=True,
                )
                LessonWord.objects.bulk_create([
                    LessonWord(lesson=lesson, word=w, translation=t, order=j)
                    for j, (w, t) in enumerate(l["words"])
                ])
                exercise_rows = []
                for j, ex in enumerate(l["exercises"]):
                    kind, prompt, answer = ex[0], ex[1], ex[2]
                    bank = ex[3] if len(ex) > 3 else []
                    exercise_rows.append(LessonExercise(
                        lesson=lesson, kind=kind, prompt=prompt, answer=answer, bank=bank, order=j,
                    ))
                LessonExercise.objects.bulk_create(exercise_rows)
                l_created += 1

            s_created = 0
            colors = ["violet", "amber", "teal", "rose", "sky", "lime"]
            for i, s in enumerate(STORIES):
                if Story.objects.filter(subject=subject, cefr_level=level, title=s["title"]).exists():
                    continue
                story = Story.objects.create(
                    subject=subject, cefr_level=level, order=i, title=s["title"], text=s["text"],
                    cover_emoji=s["emoji"], cover_color=colors[i % len(colors)], is_published=True,
                )
                StoryQuestion.objects.bulk_create([
                    StoryQuestion(story=story, question=q, options=opts_, correct=correct, order=j)
                    for j, (q, opts_, correct) in enumerate(s["questions"])
                ])
                s_created += 1

        self.stdout.write(self.style.SUCCESS(f"{l_created} ta dars, {s_created} ta hikoya qo'shildi (A1)."))
