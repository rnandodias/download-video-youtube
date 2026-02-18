# YouTube Downloader

Ferramenta de linha de comando em Python para baixar vídeos e áudios do YouTube a partir do link de compartilhamento.

## Funcionalidades

- Download de vídeo em MP4 com seleção de qualidade (best, 1080p, 720p, 480p, 360p)
- Download de áudio em MP3
- Barra de progresso no terminal
- Exibição de metadados do vídeo antes do download
- Modo interativo (sem argumentos) ou via flags CLI

## Pré-requisitos

- Python 3.8+
- [ffmpeg](https://ffmpeg.org/download.html) instalado e disponível no PATH *(necessário apenas para o modo `--audio`)*

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

## Como usar

### Modo interativo
Execute sem argumentos e cole o link quando solicitado:

```bash
python main.py
```

### Passando o link diretamente

```bash
python main.py "https://youtu.be/dQw4w9WgXcQ"
```

### Opções disponíveis

| Flag | Atalho | Descrição | Padrão |
|---|---|---|---|
| `--output PASTA` | `-o` | Pasta de destino | `./downloads` |
| `--quality QUALIDADE` | `-q` | Qualidade do vídeo: `best`, `1080p`, `720p`, `480p`, `360p` | `best` |
| `--audio` | `-a` | Baixar apenas o áudio em MP3 | — |
| `--info` | `-i` | Exibir informações sem baixar | — |

### Exemplos

```bash
# Vídeo em melhor qualidade disponível
python main.py "https://youtu.be/dQw4w9WgXcQ"

# Vídeo em 720p salvo numa pasta específica
python main.py "https://youtu.be/dQw4w9WgXcQ" --quality 720p --output ~/Videos

# Somente o áudio em MP3
python main.py "https://youtu.be/dQw4w9WgXcQ" --audio

# Ver informações do vídeo sem baixar
python main.py "https://youtu.be/dQw4w9WgXcQ" --info
```

### Saída esperada

```
Buscando informações do vídeo...

  Título:      Never Gonna Give You Up
  Duração:     3:33
  Canal:       Rick Astley
  Visualiz.:   1.500.000.000

Iniciando download — formato: MP4 (best)
Destino: ./downloads

  [####################] 100%  Concluído!

Arquivo salvo em: ./downloads/
```

## Estrutura do projeto

```
download-video-youtube/
├── main.py          # Ponto de entrada e interface CLI
├── downloader.py    # Lógica de download (yt-dlp)
├── requirements.txt # Dependências
└── .gitignore
```

## Dependências

| Pacote | Descrição |
|---|---|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Fork mantido do youtube-dl com suporte atualizado ao YouTube |

## Licença

MIT — fique à vontade para usar e modificar.
