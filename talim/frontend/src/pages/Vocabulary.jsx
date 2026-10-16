import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchVocabularyLevels } from "../api/client.js";
import "./app/ui.css";
import "./Vocabulary.css";


export default function Vocabulary({ embedded = false }) {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchVocabularyLevels()
      .then(setData)
      .catch(e => setError(e.isNetworkError ? "Internet yo'q. So'zlar internet qaytganda yuklanadi." : e.message || "Yuklab bo'lmadi."));
  }, []);

  const rec = data?.levels?.find(l => l.recommended);

  return (
    <div className="ui vocab">
      <header className="ui-head">
        <div>
          {!embedded && <h1>So'z boyligi</h1>}
          <p>CEFR darajalari bo'yicha 9 700 dan ortiq inglizcha so'z. Har kuni 10 tadan o'rganing: avval tanishasiz, keyin mashq qilasiz.</p>
        </div>
      </header>

      {error && <div className="ui-alert bad">{error}</div>}

      {rec && (
        <section className="ui-card vocab-today">
          <div className="vocab-today-level" aria-hidden="true">{rec.level}</div>
          <div className="vocab-today-body">
            <h2>Bugungi 10 ta so'z</h2>
            <p className="ui-muted">{rec.description} daraja · {rec.mastered} / {rec.total} so'z o'zlashtirilgan
              {rec.learning > 0 && ` · ${rec.learning} tasi takrorlashda`}</p>
            <div className="ui-bar ok" style={{ maxWidth: 360, margin: "12px 0 18px" }}><i style={{ width: `${Math.max(rec.percent, rec.mastered ? 1 : 0)}%` }} /></div>
            <button className="ui-btn primary" onClick={() => navigate(`/app/vocabulary/${rec.level}?mode=learn`)}>O'rganishni boshlash</button>
          </div>
        </section>
      )}

      <section>
        <h2 className="vocab-h2">Darajalar</h2>
        <div className="vocab-levels">
          {(data?.levels || []).map(l => (
            <button key={l.level} className={"ui-card vocab-level" + (l.recommended ? " rec" : "")}
              onClick={() => navigate(`/app/vocabulary/${l.level}`)} disabled={!l.total}>
              <span className="vocab-level-code">{l.level}</span>
              <span className="vocab-level-name">{l.description}</span>
              <span className="ui-bar ok"><i style={{ width: `${l.percent}%` }} /></span>
              <span className="vocab-level-count"><strong>{l.mastered}</strong> / {l.total} so'z</span>
              {l.recommended && <span className="vocab-level-badge">Siz uchun</span>}
            </button>
          ))}
          {!data && !error && [0, 1, 2, 3, 4, 5].map(i => <div key={i} className="ui-skeleton" style={{ height: 150 }} />)}
        </div>
      </section>

      <section className="vocab-extra">
        <button className="ui-card vocab-story vocab-dictlink" onClick={() => navigate("/app/dictionary")}>
          <h2>Lug'at</h2>
          <p className="ui-muted">Istalgan so'zni qidiring: tarjima, misol va talaffuz.</p>
        </button>
      </section>
    </div>
  );
}
