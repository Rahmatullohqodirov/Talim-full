
import React, { useEffect, useMemo, useState } from "react";
import { fetchFlashcards, logActivity } from "../../api/client.js";
import "./WordGame.css";

const CACHE_KEY = "st_wordgame_cache_v2";
const STAGE_SIZE = 20;

function shuffle(arr) {
  const a = [...arr];

  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }

  return a;
}

function loadCache() {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveCache(list) {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify(list));
  } catch {
    // localStorage ishlamasa ham o'yin davom etadi
  }
}

export default function WordGame({ embedded = false }) {
  const [pool, setPool] = useState(() => loadCache());
  const [usingCache, setUsingCache] = useState(false);

  const [stage, setStage] = useState(1);
  const [round, setRound] = useState([]);
  const [current, setCurrent] = useState(0);
  const [options, setOptions] = useState([]);

  const [picked, setPicked] = useState(null);
  const [score, setScore] = useState(0);
  const [finished, setFinished] = useState(false);

  const [direction, setDirection] = useState("en-uz");

  const validPool = useMemo(() => {
    return pool.filter(
      (card) =>
        card &&
        card.id !== undefined &&
        String(card.front_text || "").trim() &&
        String(card.back_text || "").trim()
    );
  }, [pool]);

  const totalStages = Math.ceil(validPool.length / STAGE_SIZE);

  const card = round[current];

  const promptText = card
    ? direction === "en-uz"
      ? card.front_text
      : card.back_text
    : "";

  /*
   * So'zni ovoz chiqarib o'qish.
   */
  function speakWord(text = promptText) {
    if (!text || !("speechSynthesis" in window)) return;

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);

    utterance.lang = direction === "en-uz" ? "en-US" : "uz-UZ";
    utterance.rate = 0.85;
    utterance.pitch = 1;

    window.speechSynthesis.speak(utterance);
  }

  /*
   * Har yangi so'z kelganda avtomatik aytiladi.
   */
  useEffect(() => {
    if (!card || finished) return;

    const timer = setTimeout(() => {
      speakWord(promptText);
    }, 350);

    return () => {
      clearTimeout(timer);
      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, [current, round, direction, finished]);

  useEffect(() => {
    fetchFlashcards()
      .then((data) => {
        const list = Array.isArray(data)
          ? data
          : data?.results || [];

        if (list.length >= 4) {
          setPool(list);
          saveCache(list);
          setUsingCache(false);
        } else {
          setUsingCache(true);
        }
      })
      .catch(() => {
        setUsingCache(true);
      });
  }, []);

  /*
   * Bosqich uchun 20 ta so'z tayyorlaymiz.
   */
  function startStage(stageNumber = stage) {
    if (validPool.length < 4) return;

    const start = (stageNumber - 1) * STAGE_SIZE;
    const stageWords = validPool.slice(start, start + STAGE_SIZE);

    let selected = stageWords;

    if (selected.length < 4) {
      selected = shuffle(validPool).slice(
        0,
        Math.min(STAGE_SIZE, validPool.length)
      );
    }

    selected = shuffle(selected);

    setStage(stageNumber);
    setRound(selected);
    setCurrent(0);
    setScore(0);
    setFinished(false);
    setPicked(null);

    buildOptions(selected, 0);
  }

  /*
   * Variantlarni yaratish.
   */
  function buildOptions(cards, index) {
    const card = cards[index];

    if (!card) {
      setOptions([]);
      return;
    }

    const correctText =
      direction === "en-uz"
        ? card.back_text
        : card.front_text;

    const wrongPool = shuffle(
      cards.filter((item) => item.id !== card.id)
    ).slice(0, 3);

    const wrongOptions = wrongPool.map((item) =>
      direction === "en-uz"
        ? item.back_text
        : item.front_text
    );

    setOptions(
      shuffle([
        correctText,
        ...wrongOptions,
      ])
    );
  }

  /*
   * Javobni tanlash.
   */
  function choose(option) {
    if (picked !== null) return;

    const card = round[current];

    if (!card) return;

    const correctText =
      direction === "en-uz"
        ? card.back_text
        : card.front_text;

    const isCorrect = option === correctText;

    setPicked({
      option,
      isCorrect,
      correctText,
    });

    if (isCorrect) {
      setScore((prev) => prev + 1);
    }

    setTimeout(() => {
      const next = current + 1;

      if (next >= round.length) {
        setFinished(true);

        const minutes = Math.max(
          1,
          Math.round((round.length * 8) / 60)
        );

        logActivity("english", minutes, 1).catch(() => {});
      } else {
        setCurrent(next);
        setPicked(null);
        buildOptions(round, next);
      }
    }, 700);
  }

  function nextStage() {
    if (stage < totalStages) {
      startStage(stage + 1);
    } else {
      startStage(1);
    }
  }

  const progress = round.length
    ? ((current + 1) / round.length) * 100
    : 0;

  return (
    <div className="wordgame-wrapper">
      <div className="wordgame-header">
        <div>
          {!embedded && <h1 className="page-title">So'z o'yini</h1>}
          <p className="page-sub">
            Bosqichma-bosqich o'yin: inglizcha so'zning tarjimasini toping va aksincha.
            {usingCache &&
              " (offlayn — saqlangan so'zlar bilan ishlayapti)"}
          </p>
        </div>

        {round.length > 0 && !finished && (
          <div className="wordgame-counter">
            <span>{current + 1}</span>
            <small>/ {round.length}</small>
          </div>
        )}
      </div>

      {validPool.length >= 4 && (
        <>
          {/* BOSQICHLAR */}
          <div className="wordgame-stages">
            <div className="wordgame-stage-title">
              🏆 Bosqichlar
            </div>

            <div className="wordgame-stage-list">
              {Array.from(
                { length: totalStages },
                (_, index) => {
                  const stageNumber = index + 1;

                  return (
                    <button
                      key={stageNumber}
                      className={
                        "wordgame-stage-btn" +
                        (stageNumber === stage ? " active" : "")
                      }
                      onClick={() => startStage(stageNumber)}
                    >
                      {stageNumber}
                    </button>
                  );
                }
              )}
            </div>
          </div>

          {/* TOOLBAR */}
          <div className="wordgame-toolbar">
            <div className="direction-toggle">
              <button
                className={
                  "direction-btn" +
                  (direction === "en-uz" ? " active" : "")
                }
                onClick={() => setDirection("en-uz")}
              >
                🇬🇧 EN → UZ
              </button>

              <button
                className={
                  "direction-btn" +
                  (direction === "uz-en" ? " active" : "")
                }
                onClick={() => setDirection("uz-en")}
              >
                🇺🇿 UZ → EN
              </button>
            </div>

            <div className="wordgame-score">
              ⭐ {score} / {round.length}
            </div>
          </div>

          {/* O'YIN */}
          {!finished && card && (
            <div className="wordgame-card">

              <div className="wordgame-card-top">
                <div className="wordgame-stage-label">
                  {stage}-bosqich
                </div>

                <div className="wordgame-step">
                  So'z {current + 1} / {round.length}
                </div>
              </div>

              {/* PROGRESS */}
              <div className="wordgame-progress-bar">
                <div
                  className="wordgame-progress-fill"
                  style={{ width: `${progress}%` }}
                />
              </div>

              {/* SO'Z */}
              <div className="wordgame-word-section">
                <div className="wordgame-word-label">
                  {direction === "en-uz"
                    ? "Inglizcha so'z"
                    : "O'zbekcha so'z"}
                </div>

                <div className="wordgame-prompt">
                  {promptText}
                </div>

                <button
                  className="wordgame-speak-btn"
                  onClick={() => speakWord(promptText)}
                  type="button"
                >
                  🔊 So'zni eshitish
                </button>
              </div>

              {/* SAVOL */}
              <div className="wordgame-question">
                To'g'ri tarjimani tanlang:
              </div>

              {/* VARIANTLAR */}
              <div className="wordgame-options">
                {options.map((opt, index) => {
                  let cls = "wordgame-option";

                  if (picked) {
                    if (opt === picked.correctText) {
                      cls += " correct";
                    } else if (opt === picked.option) {
                      cls += " wrong";
                    }
                  }

                  return (
                    <button
                      key={`${opt}-${index}`}
                      className={cls}
                      onClick={() => choose(opt)}
                      disabled={!!picked}
                    >
                      <span className="wordgame-option-number">
                        {String.fromCharCode(65 + index)}
                      </span>

                      <span>{opt}</span>

                      {picked &&
                        opt === picked.correctText && (
                          <span className="answer-icon">
                            ✓
                          </span>
                        )}

                      {picked &&
                        opt === picked.option &&
                        opt !== picked.correctText && (
                          <span className="answer-icon">
                            ✕
                          </span>
                        )}
                    </button>
                  );
                })}
              </div>

              <div className="wordgame-bottom-progress">
                <span>
                  {current + 1} / {round.length}
                </span>

                <span>
                  {Math.round(progress)}%
                </span>
              </div>
            </div>
          )}

          {/* NATIJA */}
          {finished && (
            <div className="wordgame-card wordgame-result">
              <div className="result-icon">
                🎉
              </div>

              <div className="wordgame-stage-label">
                {stage}-bosqich tugadi
              </div>

              <div className="wordgame-final-score">
                {score}
                <span> / {round.length}</span>
              </div>

              <p className="result-percent">
                Natijangiz:{" "}
                <strong>
                  {Math.round(
                    (score / round.length) * 100
                  )}
                  %
                </strong>
              </p>

              <div className="wordgame-finish-actions">
                <button
                  className="btn btn-primary"
                  onClick={() => startStage(stage)}
                >
                  🔄 Qayta o'ynash
                </button>

                {stage < totalStages && (
                  <button
                    className="btn btn-primary"
                    onClick={nextStage}
                  >
                    Keyingi bosqich →
                  </button>
                )}

                {stage === totalStages && (
                  <button
                    className="btn btn-primary"
                    onClick={nextStage}
                  >
                    🔁 Boshidan boshlash
                  </button>
                )}
              </div>
            </div>
          )}
        </>
      )}

      {validPool.length < 4 && (
        <div className="wordgame-empty">
          <div>📖</div>
          <p>
            O'yin uchun yetarli so'z topilmadi.
          </p>
          <small>
            Internetga ulanib qayta urinib ko'ring.
          </small>
        </div>
      )}
    </div>
  );
}

