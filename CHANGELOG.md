# Changelog

## 1.3.0

O pacote para colaboradores passa a abrir no Windows e no Mac.

- O pacote é um único `Abrir transcricao.html`, gerado por `scripts/build_colaboradores.py`. Não usa mais servidor local, Python nem PowerShell.
- O zip usa caminhos com `/`. O zip anterior tinha `\`, e o Mac extraía arquivos soltos sem a pasta da página; o `.command` também chegava sem permissão de execução.
- Novo seletor de idioma (Português por padrão). Sem idioma fixo, a transcrição parava após a primeira frase.
- O áudio é decodificado direto em 16 kHz, o que reduz a memória em áudios longos.
- Sem internet, a página mostra o erro em vez de ficar parada.

## 1.2.0

O colaborador não instala a ferramenta.

- A transcrição roda no navegador. O áudio não vai para um servidor.
- A pasta `Para colaboradores` separa `Windows` e `Mac`. Em cada uma, o arquivo é `Abrir transcricao`.

## 1.1.0

A transcrição passa a ser usada pelo time no Mac e no Windows, no computador ou na página web.

- Soltar ou escolher um áudio inicia a transcrição, sem um segundo clique.
- A aba **Leitura** mostra cada fala com o instante em que começa, para ler na tela, copiar ou baixar `.txt`.
- A aba **Arquivo para IA** entrega um Markdown com instruções, contexto e linha do tempo, para copiar ou baixar `.md` e enviar a uma IA.
- `run.sh` e `Iniciar.command` instalam e abrem a ferramenta no Mac. `run.bat` continua valendo no Windows.
- Os campos antigos `pure` e `timestamped` continuam na resposta da API.

Para voltar atrás, restaure a interface anterior (botão Transcrever e as abas Texto puro / Com timestamps) e remova `readable`, `ai_file`, `segments` e `meta` de `build_transcript`.
