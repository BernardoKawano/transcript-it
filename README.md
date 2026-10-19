# transcript-it

## Enviar para um colaborador

Mande o arquivo `Para colaboradores.zip`.

1. A pessoa extrai o zip (no Windows: botão direito > Extrair tudo)
2. Dá dois cliques em `Abrir transcricao.html`
3. O navegador abre. Ela escolhe o idioma e arrasta o áudio

É um único HTML: não precisa de Python, servidor ou permissão de execução, no Windows e no Mac. Na primeira vez o navegador baixa o modelo (cerca de 80 MB), então precisa de internet. O áudio é transcrito no computador dela.

Depois de mudar algo em `public/`, gere o pacote de novo:

```bash
python scripts/build_colaboradores.py
```

Ferramenta para o time transcrever áudio em dois resultados:

- **Leitura** — cada fala com o instante em que começa, para ler na tela, copiar ou baixar `.txt`
- **Arquivo para IA** — Markdown com contexto e linha do tempo, para copiar ou baixar `.md` e enviar ao ChatGPT, Claude ou Cursor

Funciona no navegador e também no computador, no Mac e no Windows.

## Versão no navegador

O zip abre essa página no computador da pessoa. A transcrição acontece no navegador e o áudio não fica armazenado.

O endereço [https://transcript-it.vercel.app](https://transcript-it.vercel.app) ainda é a versão anterior. Ele só passa a ser este fluxo depois de uma publicação.

## No computador

Requisitos: Python 3.12+ . O FFmpeg do sistema só é necessário se o ffmpeg embutido (`imageio-ffmpeg`) não cobrir o formato.

### Windows

1. Dê duplo clique em `run.bat` (ou em `Iniciar.vbs`)
2. Na primeira vez, o script cria o ambiente e instala as dependências
3. O navegador abre em http://127.0.0.1:8000
4. Arraste o áudio

### Mac

No Terminal, na pasta do projeto:

```bash
bash run.sh
```

Ou dê duplo clique em `Iniciar.command` (se o macOS bloquear, clique com o botão direito, escolha Abrir e confirme).

O navegador abre em http://127.0.0.1:8000. Arraste o áudio.

## Instalação manual

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000
```

Mac:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000
```

## Como usar

1. Arraste o arquivo para a área pontilhada, ou clique nela e escolha o arquivo
2. A transcrição começa sozinha
3. Em **Leitura**, acompanhe o texto com o tempo de cada fala
4. Em **Arquivo para IA**, copie ou baixe o `.md` e anexe numa conversa com IA

Formatos aceitos: MP3, WAV, M4A, OGG, FLAC, AAC, WMA, MP4, MKV, MOV, WEBM e outros vídeos comuns.

## Testes

```bash
pytest
```

## Deploy no Vercel

O repositório está configurado para deploy automático via GitHub:

1. Conecte o repo [transcript-it](https://github.com/BernardoKawano/transcript-it) no [Vercel Dashboard](https://vercel.com/new)
2. Cada push na branch `main` gera um novo deploy
3. URL de produção: https://transcript-it.vercel.app

Variáveis de ambiente opcionais no Vercel:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `WHISPER_MODEL` | `base` | Tamanho do modelo (`tiny`, `base`, `small`) |
| `WHISPER_DEVICE` | `cpu` | Dispositivo de inferência |
| `WHISPER_COMPUTE` | `int8` | Tipo de computação |

## Estrutura

- `main.py` — API FastAPI
- `transcriber.py` — transcrição (faster-whisper) e os dois formatos de saída
- `public/` — interface web
- `run.bat` / `Iniciar.vbs` — atalho no Windows
- `run.sh` / `Iniciar.command` — atalho no Mac
- `scripts/build_colaboradores.py` — gera a pasta e o zip `Para colaboradores`
