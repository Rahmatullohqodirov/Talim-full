// src/api/dictionaryApi.js

export async function searchWordOnline(word) {
  if (!navigator.onLine) {
    throw new Error("Internet aloqasi yo'q (Oflayn rejim)");
  }

  const cleanWord = word.trim().toLowerCase();

  // Free Dictionary API — talaffuz/phonetic uchun
  const dictRes = await fetch(`https://api.dictionaryapi.dev/api/v2/entries/en/${cleanWord}`);
  const dictData = await dictRes.json();

  // MyMemory API — O'zbekcha tarjima uchun
  const transRes = await fetch(`https://api.mymemory.translated.net/get?q=${cleanWord}&langpair=en|uz`);
  const transData = await transRes.json();

  const phonetic = dictData[0]?.phonetic || (dictData[0]?.phonetics?.find(p => p.text)?.text) || '';
  const translation = transData?.responseData?.translatedText || 'Tarjima topilmadi';

  return {
    en: cleanWord,
    uz: translation,
    phonetic: phonetic
  };
}