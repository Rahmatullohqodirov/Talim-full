// src/data/dictionaryData.js

export const initialVocabulary = [
  { id: 1, en: "hold", uz: "ushlamoq", phonetic: "[hoʊld]" },
  { id: 2, en: "read", uz: "o'qimoq", phonetic: "[riːd]" },
  { id: 3, en: "speak", uz: "gapirmoq", phonetic: "[spiːk]" },
  { id: 4, en: "apple", uz: "olma", phonetic: "[ˈæp.əl]" },
  { id: 5, en: "book", uz: "kitob", phonetic: "[bʊk]" },
  { id: 6, en: "water", uz: "suv", phonetic: "[ˈwɔː.tər]" },
  { id: 7, en: "friend", uz: "do'st", phonetic: "[frend]" },
  { id: 8, en: "work", uz: "ishlamoq", phonetic: "[wɜːrk]" }
];

export const lessonsList = [
  {
    id: 1,
    title: "1 - Dars. Fe'lning asosiy shakli",
    vocab: [
      { en: "hold", uz: "ushlamoq" },
      { en: "read", uz: "o'qimoq" },
      { en: "write", uz: "yozmoq" }
    ],
    sentences: [
      { uz: "U (erkak) ushlamaydi.", en: "he does not hold", options: ["he", "does", "not", "hold", "she", "will"] },
      { uz: "U (ayol) o'qiyapti.", en: "she is reading", options: ["she", "is", "reading", "he", "reads"] }
    ]
  },
  {
    id: 2,
    title: "2 - Dars. So'roq so'zlar",
    vocab: [
      { en: "what", uz: "nima" },
      { en: "where", uz: "qayerda" },
      { en: "who", uz: "kim" }
    ],
    sentences: [
      { uz: "Siz kimsiz?", en: "who are you", options: ["who", "are", "you", "what", "is"] }
    ]
  }
];