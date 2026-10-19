const LANGUAGE_NAMES = {
  pt: "português",
  en: "inglês",
  es: "espanhol",
  fr: "francês",
  de: "alemão",
  it: "italiano",
  ja: "japonês",
  ko: "coreano",
  zh: "chinês",
  ru: "russo",
  ar: "árabe",
  nl: "holandês",
  pl: "polonês",
  sv: "sueco",
  tr: "turco",
  hi: "hindi",
  uk: "ucraniano",
};

export const SHARE_URL = "https://transcript-it.vercel.app";

function pad(value, size = 2) {
  return String(value).padStart(size, "0");
}

export function formatTime(seconds) {
  const safe = Number(seconds) || 0;
  const h = Math.floor(safe / 3600);
  const m = Math.floor((safe % 3600) / 60);
  const s = (safe % 60).toFixed(3).padStart(6, "0");
  if (h > 0) return `${pad(h)}:${pad(m)}:${s}`;
  return `${pad(m)}:${s}`;
}

export function formatClock(seconds) {
  const total = Math.max(0, Math.floor(Number(seconds) || 0));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  if (h) return `${pad(h)}:${pad(m)}:${pad(s)}`;
  return `${pad(m)}:${pad(s)}`;
}

export function formatDurationLabel(seconds) {
  const total = Math.max(0, Math.round(Number(seconds) || 0));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  const parts = [];
  if (h) parts.push(`${h} h`);
  if (m) parts.push(`${m} min`);
  if (s || !parts.length) parts.push(`${s} s`);
  return parts.join(" ");
}

export function languageLabel(code) {
  if (!code) return "idioma não identificado";
  return LANGUAGE_NAMES[code] || code;
}

export function countLabel(n) {
  return n === 1 ? "1 trecho" : `${n} trechos`;
}

export function yamlQuote(value) {
  const escaped = String(value).replace(/\\/g, "\\\\").replace(/"/g, '\\"');
  return `"${escaped}"`;
}

export function asRows(segments) {
  const rows = [];
  for (const seg of segments || []) {
    const start = Array.isArray(seg) ? seg[0] : seg.start;
    const end = Array.isArray(seg) ? seg[1] : seg.end;
    const text = String(Array.isArray(seg) ? seg[2] : seg.text || "").trim();
    if (!text) continue;
    rows.push([Number(start) || 0, Number(end) || 0, text]);
  }
  return rows;
}

export function isoLocal(date) {
  const value = date instanceof Date ? date : new Date(date);
  const tz = -value.getTimezoneOffset();
  const sign = tz >= 0 ? "+" : "-";
  const abs = Math.abs(tz);
  return (
    `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}` +
    `T${pad(value.getHours())}:${pad(value.getMinutes())}:${pad(value.getSeconds())}` +
    `${sign}${pad(Math.floor(abs / 60))}:${pad(abs % 60)}`
  );
}

export function buildReadable(segments, { filename, language, duration }) {
  const rows = asRows(segments);
  const total = duration != null ? duration : rows.length ? rows[rows.length - 1][1] : 0;
  const lines = [
    filename,
    `${formatDurationLabel(total)} · ${languageLabel(language)} · ${countLabel(rows.length)}`,
    "",
  ];
  if (!rows.length) {
    lines.push("Nenhuma fala detectada.", "");
    return lines.join("\n");
  }
  for (const [start, , text] of rows) {
    lines.push(formatClock(start), text, "");
  }
  return lines.join("\n");
}

export function buildAiFile(segments, { filename, language, duration, generatedAt }) {
  const rows = asRows(segments);
  const total = duration != null ? duration : rows.length ? rows[rows.length - 1][1] : 0;
  const stamp = typeof generatedAt === "string" ? generatedAt : isoLocal(generatedAt || new Date());
  const lines = [
    "---",
    "tipo: transcricao",
    `origem: ${yamlQuote(filename)}`,
    `idioma: ${language || "desconhecido"}`,
    `duracao_segundos: ${Number(total).toFixed(3)}`,
    `segmentos: ${rows.length}`,
    `gerado_em: ${stamp}`,
    "---",
    "",
    "# Transcrição para IA",
    "",
    "Este arquivo é a transcrição integral de um áudio.",
    "Use apenas o que está escrito abaixo.",
    "Se uma informação não aparecer na transcrição, diga que ela não consta.",
    "Não invente falas, nomes, decisões ou números.",
    "",
    "## Contexto",
    "",
    `- Arquivo: ${filename}`,
    `- Duração: ${formatDurationLabel(total)}`,
    `- Idioma: ${languageLabel(language)}`,
    `- Trechos: ${rows.length}`,
    "",
    "## Texto",
    "",
  ];
  if (rows.length) lines.push(...rows.map((row) => row[2]));
  else lines.push("Nenhuma fala detectada.");
  lines.push("", "## Linha do tempo", "");
  if (rows.length) {
    for (const [start, end, text] of rows) {
      lines.push(`- [${formatTime(start)}–${formatTime(end)}] (${(end - start).toFixed(2)}s) ${text}`);
    }
  } else {
    lines.push("- Nenhuma fala detectada.");
  }
  lines.push("");
  return lines.join("\n");
}

export function buildTranscript(segments, options) {
  const rows = asRows(segments);
  const total = options.duration != null ? options.duration : rows.length ? rows[rows.length - 1][1] : 0;
  const settings = { ...options, duration: total };
  return {
    readable: buildReadable(rows, settings),
    ai_file: buildAiFile(rows, settings),
    segments: rows.map(([start, end, text]) => ({
      start: Math.round(start * 1000) / 1000,
      end: Math.round(end * 1000) / 1000,
      label: formatClock(start),
      text,
    })),
    meta: {
      filename: options.filename,
      language: options.language || null,
      language_label: languageLabel(options.language),
      duration: Math.round(total * 1000) / 1000,
      duration_label: formatDurationLabel(total),
      segment_count: rows.length,
    },
  };
}
