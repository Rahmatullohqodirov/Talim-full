import React from "react";

/**
 * AI javobi uchun yengil markdown: **qalin**, *kursiv*, `kod`, ro'yxatlar va paragraflar.
 * HTML ishlatilmaydi (dangerouslySetInnerHTML yo'q), shuning uchun xavfsiz.
 */
const INLINE = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*\s][^*]*\*|_[^_\s][^_]*_)/g;

function inline(text, keyPrefix) {
  return text.split(INLINE).map((part, i) => {
    const key = `${keyPrefix}-${i}`;
    if (/^\*\*[^*]+\*\*$/.test(part)) return <strong key={key}>{part.slice(2, -2)}</strong>;
    if (/^`[^`]+`$/.test(part)) return <code key={key}>{part.slice(1, -1)}</code>;
    if (/^(\*[^*]+\*|_[^_]+_)$/.test(part)) return <em key={key}>{part.slice(1, -1)}</em>;
    return part;
  });
}

const BULLET = /^\s*[-*•]\s+/;
const NUMBERED = /^\s*\d+[.)]\s+/;

// Blok ichidagi qatorlarni guruhlaydi: ketma-ket ro'yxat qatorlari -> ro'yxat, qolganlari -> paragraf
function groupLines(lines) {
  const groups = [];
  for (const line of lines) {
    const kind = BULLET.test(line) ? "ul" : NUMBERED.test(line) ? "ol" : "p";
    const last = groups[groups.length - 1];
    if (last && last.kind === kind) last.lines.push(line);
    else groups.push({ kind, lines: [line] });
  }
  return groups;
}

export default function RichText({ text }) {
  const blocks = String(text || "").replace(/\r/g, "").split(/\n{2,}/);
  return blocks.flatMap((block, bi) => {
    const lines = block.split("\n").filter(l => l.trim() !== "");
    return groupLines(lines).map((g, gi) => {
      const key = `${bi}-${gi}`;
      if (g.kind === "ul") {
        return <ul key={key}>{g.lines.map((l, i) => <li key={i}>{inline(l.replace(BULLET, ""), `${key}-${i}`)}</li>)}</ul>;
      }
      if (g.kind === "ol") {
        return <ol key={key}>{g.lines.map((l, i) => <li key={i}>{inline(l.replace(NUMBERED, ""), `${key}-${i}`)}</li>)}</ol>;
      }
      return (
        <p key={key}>
          {g.lines.map((l, i) => (
            <React.Fragment key={i}>
              {i > 0 && <br />}
              {inline(l.replace(/^#{1,6}\s+/, ""), `${key}-${i}`)}
            </React.Fragment>
          ))}
        </p>
      );
    });
  });
}
