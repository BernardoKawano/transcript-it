import { buildTranscript } from "./format.js";

const TRANSFORMERS_URL = "https://cdn.jsdelivr.net/npm/@xenova/transformers@2.17.2";
// Sem idioma fixo, o Whisper no navegador para após a primeira frase.
const WHISPER_LANGUAGES = { pt: "portuguese", en: "english", es: "spanish" };

const fileInput = document.getElementById("fileInput");
const dropZone = document.getElementById("dropZone");
const dropLabel = document.getElementById("dropLabel");
const fileName = document.getElementById("fileName");
const btnClear = document.getElementById("btnClear");
const statusBar = document.getElementById("statusBar");
const results = document.getElementById("results");
const metaLine = document.getElementById("metaLine");
const segmentList = document.getElementById("segmentList");
const aiFile = document.getElementById("aiFile");
const languageSelect = document.getElementById("languageSelect");

let current = null;
let runId = 0;
let modelPromise = null;

function setStatus(msg, type = "") {
  if (!msg) {
    statusBar.textContent = "";
    statusBar.className = "status-bar hidden";
    return;
  }
  statusBar.className = "status-bar " + type;
  if (type === "loading") {
    statusBar.innerHTML = '<span class="spinner" aria-hidden="true"></span><span>' + escapeHtml(msg) + "</span>";
  } else {
    statusBar.textContent = msg;
  }
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function stemOf(name) {
  const base = String(name || "transcricao").replace(/\.[^.]+$/, "") || "transcricao";
  return base.replace(/[\\/:*?"<>|]/g, "-").trim() || "transcricao";
}

function formatBytes(bytes) {
  if (!Number.isFinite(bytes) || bytes < 0) return "";
  if (bytes < 1024 * 1024) return Math.max(1, Math.round(bytes / 1024)) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function showCopied(id) {
  const badge = document.getElementById(id);
  badge.classList.add("show");
  setTimeout(() => badge.classList.remove("show"), 1500);
}

async function copyText(text, badgeId) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const area = document.createElement("textarea");
    area.value = text;
    document.body.appendChild(area);
    area.select();
    document.execCommand("copy");
    area.remove();
  }
  showCopied(badgeId);
}

function downloadText(filename, content, mime) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function renderTranscript(data) {
  current = data;
  const meta = data.meta || {};
  const count = meta.segment_count ?? (data.segments || []).length;
  const countText = count === 1 ? "1 trecho" : count + " trechos";
  metaLine.textContent = [meta.filename, meta.duration_label, meta.language_label, countText]
    .filter(Boolean)
    .join(" · ");

  segmentList.replaceChildren();
  const segments = data.segments || [];
  if (!segments.length) {
    const empty = document.createElement("li");
    empty.className = "segment segment-empty";
    empty.textContent = "Nenhuma fala detectada.";
    segmentList.appendChild(empty);
  } else {
    for (const seg of segments) {
      const item = document.createElement("li");
      item.className = "segment";
      const time = document.createElement("time");
      time.textContent = seg.label || "";
      const text = document.createElement("p");
      text.textContent = seg.text || "";
      item.append(time, text);
      segmentList.appendChild(item);
    }
  }

  aiFile.textContent = data.ai_file || "";
  results.classList.add("visible");
  results.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// Aberto direto do disco (file://), alguns navegadores bloqueiam o Cache Storage.
async function browserCacheWorks() {
  try {
    await caches.open("transformers-cache");
    return true;
  } catch {
    return false;
  }
}

async function createModel(onProgress) {
  let transformers;
  try {
    transformers = await import(TRANSFORMERS_URL);
  } catch {
    throw new Error("Sem conexão para baixar o transcritor. Verifique a internet e tente de novo.");
  }
  const { pipeline, env } = transformers;
  env.allowLocalModels = false;
  env.useBrowserCache = await browserCacheWorks();
  try {
    return await pipeline("automatic-speech-recognition", "Xenova/whisper-base", {
      progress_callback: onProgress,
    });
  } catch (err) {
    if (err instanceof TypeError) {
      throw new Error("Não foi possível baixar o modelo. Verifique a internet e tente de novo.");
    }
    throw err;
  }
}

function loadModel(onProgress) {
  if (!modelPromise) {
    modelPromise = createModel(onProgress).catch((err) => {
      modelPromise = null;
      throw err;
    });
  }
  return modelPromise;
}

async function decodeTo16k(file) {
  // Decodifica direto em 16 kHz: um áudio de 1 h ocupa ~230 MB em vez de ~1,4 GB.
  const audioCtx = new AudioContext({ sampleRate: 16000 });
  try {
    const decoded = await audioCtx.decodeAudioData(await file.arrayBuffer());
    const channels = decoded.numberOfChannels;
    let samples = decoded.getChannelData(0);
    if (channels > 1) {
      const mono = new Float32Array(decoded.length);
      for (let c = 0; c < channels; c++) {
        const data = decoded.getChannelData(c);
        for (let i = 0; i < data.length; i++) mono[i] += data[i] / channels;
      }
      samples = mono;
    }
    return { samples, duration: decoded.duration };
  } finally {
    await audioCtx.close();
  }
}

function chunksToRows(output, duration) {
  const chunks = output && output.chunks;
  if (!chunks || !chunks.length) {
    const text = String((output && output.text) || "").trim();
    return text ? [[0, duration || 0, text]] : [];
  }
  const rows = [];
  for (let i = 0; i < chunks.length; i++) {
    const chunk = chunks[i];
    const text = String(chunk.text || "").trim();
    if (!text) continue;
    const stamp = chunk.timestamp || [0, null];
    const start = Number(stamp[0]) || 0;
    let end = stamp[1] == null ? null : Number(stamp[1]);
    if (end == null) {
      const next = chunks[i + 1] && chunks[i + 1].timestamp;
      end = next && next[0] != null ? Number(next[0]) : duration || start;
    }
    rows.push([start, end, text]);
  }
  return rows;
}

async function transcribe(file) {
  if (!file) return;
  const id = ++runId;
  current = null;
  fileName.textContent = file.name;
  fileName.classList.add("visible");
  results.classList.remove("visible");
  dropZone.classList.add("busy");

  const size = formatBytes(file.size);
  const label = size ? file.name + " (" + size + ")" : file.name;
  setStatus("Preparando " + label + "…", "loading");

  try {
    const { samples, duration } = await decodeTo16k(file);
    if (id !== runId) return;

    const model = await loadModel((data) => {
      if (id !== runId) return;
      if (data && data.status === "progress") {
        const pct = data.progress == null ? "" : " " + Math.round(data.progress) + "%";
        setStatus("Baixando o modelo" + pct + "… só na primeira vez, cerca de 80 MB.", "loading");
      }
    });
    if (id !== runId) return;

    setStatus("Transcrevendo " + label + " neste computador…", "loading");
    const language = WHISPER_LANGUAGES[languageSelect.value] ? languageSelect.value : "pt";
    const output = await model(samples, {
      return_timestamps: true,
      task: "transcribe",
      language: WHISPER_LANGUAGES[language],
      chunk_length_s: 30,
      stride_length_s: 5,
    });
    if (id !== runId) return;

    renderTranscript(buildTranscript(chunksToRows(output, duration), {
      filename: file.name,
      language,
      duration,
      generatedAt: new Date(),
    }));
    setStatus("Transcrição pronta. Escolha Leitura ou Arquivo para IA.", "ok");
  } catch (err) {
    if (id !== runId) return;
    const message = err && err.name === "EncodingError"
      ? "O navegador não conseguiu ler esse arquivo. Use MP3, WAV, M4A ou OGG."
      : (err && err.message) || "Falha ao transcrever.";
    setStatus(message, "error");
  } finally {
    if (id === runId) dropZone.classList.remove("busy");
  }
}

fileInput.addEventListener("change", (e) => {
  const file = e.target.files[0];
  fileInput.value = "";
  if (file) transcribe(file);
});

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("dragover");
  dropLabel.textContent = "Solte para transcrever";
});
dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("dragover");
  dropLabel.textContent = "Arraste o áudio aqui";
});
dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  e.stopPropagation();
  dropZone.classList.remove("dragover");
  dropLabel.textContent = "Arraste o áudio aqui";
  const file = e.dataTransfer.files[0];
  if (file) transcribe(file);
});

window.addEventListener("dragover", (e) => e.preventDefault());
window.addEventListener("drop", (e) => {
  e.preventDefault();
  const file = e.dataTransfer && e.dataTransfer.files[0];
  if (file) transcribe(file);
});

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    const target = tab.dataset.tab;
    document.querySelectorAll(".tab").forEach((t) => {
      const active = t.dataset.tab === target;
      t.classList.toggle("active", active);
      t.setAttribute("aria-selected", active);
    });
    document.querySelectorAll(".result-panel").forEach((panel) => {
      const active = panel.id === "panel-" + target;
      panel.classList.toggle("active", active);
      panel.hidden = !active;
    });
  });
});

btnClear.addEventListener("click", () => {
  runId += 1;
  current = null;
  fileInput.value = "";
  fileName.textContent = "";
  fileName.classList.remove("visible");
  segmentList.replaceChildren();
  aiFile.textContent = "";
  metaLine.textContent = "";
  results.classList.remove("visible");
  dropZone.classList.remove("busy");
  setStatus("");
});

document.getElementById("btnCopyReadable").addEventListener("click", () => {
  if (!current) return;
  copyText(current.readable || "", "copiedReadable");
});

document.getElementById("btnCopyAi").addEventListener("click", () => {
  if (!current) return;
  copyText(current.ai_file || "", "copiedAi");
});

document.getElementById("btnDownloadReadable").addEventListener("click", () => {
  if (!current) return;
  const name = stemOf(current.meta && current.meta.filename) + "-leitura.txt";
  downloadText(name, current.readable || "", "text/plain;charset=utf-8");
});

document.getElementById("btnDownloadAi").addEventListener("click", () => {
  if (!current) return;
  const name = stemOf(current.meta && current.meta.filename) + "-para-ia.md";
  downloadText(name, current.ai_file || "", "text/markdown;charset=utf-8");
});
