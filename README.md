# Video Downloader (YouTube / Instagram)

Ferramenta de linha de comando em Python para baixar vídeos e áudios do YouTube e do Instagram, com suporte a transcrição automática, tradução e resumo gerado por IA.

## Funcionalidades

- Download de vídeos do **YouTube** e do **Instagram** (reels e posts com vídeo)
- Download de vídeo em MP4 com seleção de qualidade (best, 1080p, 720p, 480p, 360p)
- Download de áudio em MP3
- Barra de progresso no terminal
- Exibição de metadados do vídeo antes do download
- Modo interativo (sem argumentos) ou via flags CLI
- **Transcrição automática** com Whisper (OpenAI) — detecta o idioma automaticamente
- **Tradução + resumo detalhado** via IA, com suporte a múltiplos provedores: Anthropic (Claude), OpenAI (GPT) e Google (Gemini)
- Processamento de arquivos já existentes na pasta `downloads/`

## Pré-requisitos

- Python 3.8+
- [ffmpeg](https://ffmpeg.org/download.html) instalado e disponível no PATH

## Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/<seu-usuario>/download-video-youtube.git
cd download-video-youtube

# 2. Crie e ative o ambiente virtual
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt
```

> **Atenção:** o `openai-whisper` instala o PyTorch (~2 GB). Na primeira execução com o modelo `large`, o Whisper fará o download do modelo (~1,5 GB) automaticamente.

## Configuração das chaves de API

Copie o arquivo de exemplo e preencha as chaves dos provedores que for usar:

```bash
cp .env.example .env
```

```env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
```

Você só precisa preencher a chave do provedor que for usar.

## Instagram: cookies de sessão

O Instagram exige login para baixar a maioria dos vídeos, inclusive reels públicos. A ferramenta não usa usuário e senha: ela reaproveita os **cookies** de uma sessão em que você já está logado no navegador.

1. Instale a extensão **[Get cookies.txt LOCALLY](https://github.com/kairi003/Get-cookies.txt-LOCALLY)** (código aberto, não envia dados para fora do computador).
2. Abra o `instagram.com` logado na sua conta, clique na extensão e exporte.
3. Salve o arquivo como `cookies.txt` na pasta do projeto.

O arquivo é usado automaticamente quando existe. Para usar outro caminho, informe `--cookies ARQUIVO` ou defina `COOKIES_FILE` no `.env`.

> **Atenção:** o `cookies.txt` dá acesso à sua conta, assim como a senha. Ele já está no `.gitignore` — nunca o compartilhe nem o versione. Se ele parar de funcionar (sessão expirada), exporte de novo.

## Como usar

### Download simples

```bash
# Modo interativo (cola o link quando solicitado)
python main.py

# Passando o link diretamente
python main.py "https://youtu.be/mpALXah_PBg"

# Instagram (usa ./cookies.txt automaticamente)
python main.py "https://www.instagram.com/reel/XXXXXXXXXXX/"
```

### Vídeo compatível para compartilhar

Alguns vídeos vêm em codecs como VP9 ou AV1, que certos apps e editores não abrem. Com `--compat`, o arquivo é convertido para **H.264 + AAC**, aceito por WhatsApp, Teams, iPhone, Android e editores de vídeo:

```bash
python main.py "https://www.instagram.com/reel/XXXXXXXXXXX/" --compat
```

Só o que não for compatível é recodificado (o que já for é copiado sem perda), e o arquivo convertido substitui o original.

Parâmetros de rastreamento dos links de compartilhamento (`utm_*`, `si`, `igsh`, `srtk`...) são removidos automaticamente.

### Download + transcrição e resumo

```bash
# Baixar e já transcrever/resumir (usa Anthropic Claude por padrão)
python main.py "https://youtu.be/dQw4w9WgXcQ" --transcribe

# Escolhendo o provedor e o modelo
python main.py "https://youtu.be/dQw4w9WgXcQ" --transcribe --provider openai --model gpt-4o
python main.py "https://youtu.be/dQw4w9WgXcQ" --transcribe --provider gemini --model gemini-2.0-flash
python main.py "https://youtu.be/dQw4w9WgXcQ" --transcribe --provider anthropic --model claude-opus-4-6
```

### Processar um arquivo já existente

```bash
# Transcrever e resumir um vídeo ou áudio que já está na pasta downloads
python main.py --process downloads/meu_video.mp4
python main.py --process downloads/meu_audio.mp3 --provider openai
```

### Opções disponíveis

| Flag | Atalho | Descrição | Padrão |
| --- | --- | --- | --- |
| `--output PASTA` | `-o` | Pasta de destino | `./downloads` |
| `--quality QUALIDADE` | `-q` | Qualidade: `best`, `1080p`, `720p`, `480p`, `360p` | `best` |
| `--audio` | `-a` | Baixar apenas o áudio em MP3 | — |
| `--info` | `-i` | Exibir informações sem baixar | — |
| `--compat` | — | Converter para H.264 + AAC (WhatsApp, Teams etc.) | — |
| `--cookies ARQUIVO` | `-c` | Arquivo `cookies.txt` de uma sessão logada | `COOKIES_FILE` ou `./cookies.txt` |
| `--transcribe` | — | Transcrever e resumir após o download | — |
| `--process ARQUIVO` | — | Transcrever/resumir arquivo existente (sem download) | — |
| `--provider PROVEDOR` | — | Provedor de IA: `anthropic`, `openai`, `gemini` | `anthropic` |
| `--model MODELO` | — | Modelo de IA a usar | varia por provedor |
| `--whisper-model WHISPER` | — | Modelo Whisper: `tiny`, `base`, `small`, `medium`, `large` | `large` |

### Modelos padrão por provedor

| Provedor | Modelo padrão |
| --- | --- |
| `anthropic` | `claude-sonnet-4-6` |
| `openai` | `gpt-4o` |
| `gemini` | `gemini-2.0-flash` |

### Saída da transcrição

O resultado é salvo em um arquivo `.txt` no mesmo local do vídeo/áudio, com o sufixo `_resumo`:

```
downloads/
├── Meu Video [dQw4w9WgXcQ].mp4
└── Meu Video [dQw4w9WgXcQ]_resumo.txt   ← transcrição original + tradução (se necessário) + resumo
```

O ID do vídeo entre colchetes evita que vídeos com o mesmo título (comum no Instagram, ex.: "Video by usuario") se sobrescrevam.

## Estrutura do projeto

```
download-video-youtube/
├── main.py          # Ponto de entrada e interface CLI
├── downloader.py    # Lógica de download (yt-dlp)
├── transcriber.py   # Transcrição com Whisper
├── summarizer.py    # Tradução e resumo com IA (multi-provedor)
├── .env.example     # Modelo para as chaves de API e cookies
├── requirements.txt # Dependências
└── .gitignore
```

## Dependências

| Pacote | Descrição |
| --- | --- |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Download de vídeos do YouTube e do Instagram |
| [openai-whisper](https://github.com/openai/whisper) | Transcrição de áudio/vídeo |
| [anthropic](https://github.com/anthropics/anthropic-sdk-python) | SDK Claude (Anthropic) |
| [openai](https://github.com/openai/openai-python) | SDK GPT (OpenAI) |
| [google-generativeai](https://github.com/google/generative-ai-python) | SDK Gemini (Google) |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Leitura do arquivo `.env` |

## Licença

MIT — fique à vontade para usar e modificar.
