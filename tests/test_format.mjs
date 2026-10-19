import assert from "node:assert/strict";
import { buildAiFile, buildReadable, buildTranscript } from "../public/static/format.js";

const REUNIAO = [
  [0.0, 4.2, "Bom dia, pessoal. Vamos revisar o áudio da reunião."],
  [4.2, 9.8, "O combinado é enviar a transcrição para o time ainda hoje."],
  [72.5, 80.0, "Ficou definido que o arquivo para IA sai em Markdown."],
];

const GERADO_EM = "2026-09-23T13:22:00-03:00";

const readable = buildReadable(REUNIAO, {
  filename: "reuniao-produto.mp3",
  language: "pt",
  duration: 80,
});

assert.equal(
  readable,
  "reuniao-produto.mp3\n" +
    "1 min 20 s · português · 3 trechos\n" +
    "\n" +
    "00:00\n" +
    "Bom dia, pessoal. Vamos revisar o áudio da reunião.\n" +
    "\n" +
    "00:04\n" +
    "O combinado é enviar a transcrição para o time ainda hoje.\n" +
    "\n" +
    "01:12\n" +
    "Ficou definido que o arquivo para IA sai em Markdown.\n",
);

const ai = buildAiFile(REUNIAO, {
  filename: 'reuniao "produto".mp3',
  language: "pt",
  duration: 80,
  generatedAt: GERADO_EM,
});

assert.equal(
  ai,
  "---\n" +
    "tipo: transcricao\n" +
    'origem: "reuniao \\"produto\\".mp3"\n' +
    "idioma: pt\n" +
    "duracao_segundos: 80.000\n" +
    "segmentos: 3\n" +
    "gerado_em: 2026-09-23T13:22:00-03:00\n" +
    "---\n" +
    "\n" +
    "# Transcrição para IA\n" +
    "\n" +
    "Este arquivo é a transcrição integral de um áudio.\n" +
    "Use apenas o que está escrito abaixo.\n" +
    "Se uma informação não aparecer na transcrição, diga que ela não consta.\n" +
    "Não invente falas, nomes, decisões ou números.\n" +
    "\n" +
    "## Contexto\n" +
    "\n" +
    '- Arquivo: reuniao "produto".mp3\n' +
    "- Duração: 1 min 20 s\n" +
    "- Idioma: português\n" +
    "- Trechos: 3\n" +
    "\n" +
    "## Texto\n" +
    "\n" +
    "Bom dia, pessoal. Vamos revisar o áudio da reunião.\n" +
    "O combinado é enviar a transcrição para o time ainda hoje.\n" +
    "Ficou definido que o arquivo para IA sai em Markdown.\n" +
    "\n" +
    "## Linha do tempo\n" +
    "\n" +
    "- [00:00.000–00:04.200] (4.20s) Bom dia, pessoal. Vamos revisar o áudio da reunião.\n" +
    "- [00:04.200–00:09.800] (5.60s) O combinado é enviar a transcrição para o time ainda hoje.\n" +
    "- [01:12.500–01:20.000] (7.50s) Ficou definido que o arquivo para IA sai em Markdown.\n",
);

const payload = buildTranscript(REUNIAO, {
  filename: "reuniao-produto.mp3",
  language: "pt",
  duration: 80,
  generatedAt: GERADO_EM,
});
assert.equal(payload.segments[2].label, "01:12");
assert.equal(payload.meta.segment_count, 3);

console.log("format.js ok");
