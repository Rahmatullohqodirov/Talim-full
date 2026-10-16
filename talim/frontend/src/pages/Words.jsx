import React from "react";
import { useSearchParams } from "react-router-dom";
import Vocabulary from "./Vocabulary.jsx";
import Flashcards from "./app/Flashcards.jsx";
import WordGame from "./app/WordGame.jsx";
import "./app/ui.css";

/**
 * "So'zlar" — bitta bo'lim, uch xil mashq:
 *  - O'rganish: CEFR darajalari bo'yicha yangi so'zlar (tanishuv + mashq)
 *  - Takrorlash: flashcard (oraliqli takrorlash)
 *  - O'yin: bosqichli so'z o'yini
 * Avval bular menyuda uchta alohida bo'lim bo'lib, bir-biriga juda o'xshab ketgan edi.
 */
const TABS = [
  { key: "learn", label: "O'rganish", hint: "Yangi so'zlar" },
  { key: "cards", label: "Takrorlash", hint: "Flashcard" },
  { key: "game", label: "O'yin", hint: "Bosqichli" },
];

export default function Words() {
  const [params, setParams] = useSearchParams();
  const tab = TABS.some(t => t.key === params.get("tab")) ? params.get("tab") : "learn";

  return (
    <div className="ui words">
      <header className="ui-head" style={{ marginBottom: 14 }}>
        <div>
          <h1>So'zlar</h1>
        </div>
        <nav className="ui-tabs" role="tablist" aria-label="So'z mashqlari">
          {TABS.map(t => (
            <button key={t.key} role="tab" aria-selected={tab === t.key} className={tab === t.key ? "on" : ""}
              onClick={() => setParams(t.key === "learn" ? {} : { tab: t.key })}>
              {t.label}
            </button>
          ))}
        </nav>
      </header>
      {tab === "learn" && <Vocabulary embedded />}
      {tab === "cards" && <Flashcards embedded />}
      {tab === "game" && <WordGame embedded />}
    </div>
  );
}
