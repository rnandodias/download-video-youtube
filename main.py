#!/usr/bin/env python3
"""
YouTube Downloader — baixe vídeos ou áudio do YouTube com um único comando.

Uso básico:
    python main.py <url>

Exemplos:
    python main.py "https://youtu.be/dQw4w9WgXcQ"
    python main.py "https://youtu.be/dQw4w9WgXcQ" --quality 720p
    python main.py "https://youtu.be/dQw4w9WgXcQ" --audio
    python main.py "https://youtu.be/dQw4w9WgXcQ" --transcribe --provider anthropic
    python main.py --process downloads/video.mp4 --provider openai --model gpt-4o
"""

import argparse
import os
import sys

import yt_dlp

from downloader import download_audio, download_video, get_video_info

VALID_QUALITIES = ["best", "1080p", "720p", "480p", "360p"]
VALID_PROVIDERS = ["anthropic", "openai", "gemini"]
VALID_WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]
DEFAULT_OUTPUT = "./downloads"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="yt-downloader",
        description="Baixa vídeos ou áudio do YouTube a partir do link de compartilhamento.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "url",
        nargs="?",
        help="Link do vídeo no YouTube (ex: https://youtu.be/xxxxx)",
    )
    parser.add_argument(
        "-o", "--output",
        default=DEFAULT_OUTPUT,
        metavar="PASTA",
        help=f"Pasta de destino dos arquivos (padrão: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "-q", "--quality",
        default="best",
        choices=VALID_QUALITIES,
        metavar="QUALIDADE",
        help=f"Qualidade do vídeo: {', '.join(VALID_QUALITIES)} (padrão: best)",
    )
    parser.add_argument(
        "-a", "--audio",
        action="store_true",
        help="Baixar apenas o áudio em MP3 (requer ffmpeg instalado)",
    )
    parser.add_argument(
        "-i", "--info",
        action="store_true",
        help="Exibir informações do vídeo sem fazer o download",
    )

    # --- Transcrição e resumo ---
    parser.add_argument(
        "--transcribe",
        action="store_true",
        help="Transcrever e resumir o vídeo após o download",
    )
    parser.add_argument(
        "--process",
        metavar="ARQUIVO",
        help="Transcrever e resumir um arquivo existente na pasta downloads (ignora URL e download)",
    )
    parser.add_argument(
        "--provider",
        choices=VALID_PROVIDERS,
        default="anthropic",
        metavar="PROVEDOR",
        help=f"Provedor de IA para tradução e resumo: {', '.join(VALID_PROVIDERS)} (padrão: anthropic)",
    )
    parser.add_argument(
        "--model",
        default=None,
        metavar="MODELO",
        help="Modelo de IA a usar (padrão: claude-sonnet-4-6 / gpt-4o / gemini-2.0-flash)",
    )
    parser.add_argument(
        "--whisper-model",
        default="large",
        choices=VALID_WHISPER_MODELS,
        metavar="WHISPER",
        dest="whisper_model",
        help=f"Modelo Whisper para transcrição: {', '.join(VALID_WHISPER_MODELS)} (padrão: large)",
    )

    return parser.parse_args()


def ask_url() -> str:
    print("=" * 50)
    print("  YouTube Downloader")
    print("=" * 50)
    url = input("\nCole o link do vídeo: ").strip()
    if not url:
        print("Nenhum link informado. Encerrando.")
        sys.exit(0)
    return url


def print_info(info: dict) -> None:
    print(f"\n  Título:      {info['title']}")
    print(f"  Duração:     {info['duration']}")
    print(f"  Canal:       {info['uploader']}")
    views = f"{info['view_count']:,}".replace(",", ".") if info["view_count"] else "?"
    print(f"  Visualiz.:   {views}")


def run_ai_pipeline(
    file_path: str,
    provider: str,
    model: str,
    whisper_model: str,
) -> None:
    """Transcreve o arquivo e gera tradução + resumo com IA."""
    from transcriber import transcribe
    from summarizer import summarize, DEFAULT_MODELS

    print(f"\nIniciando pipeline de transcrição e resumo...")

    result = transcribe(file_path, model_size=whisper_model)
    transcript = result["text"]
    language = result["language"]

    print(f"  Idioma detectado: {language}")

    effective_model = model or DEFAULT_MODELS[provider]
    print(f"  Gerando resumo com {provider} / {effective_model}...")

    summary = summarize(transcript, language, provider, model)

    base = os.path.splitext(file_path)[0]
    output_path = f"{base}_resumo.txt"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# Transcrição Original\n\n{transcript}\n\n---\n\n{summary}")

    print(f"\n  Resultado salvo em: {output_path}")


def main() -> None:
    args = parse_args()

    # Modo --process: processa arquivo existente, sem download
    if args.process:
        if not os.path.exists(args.process):
            print(f"Arquivo não encontrado: {args.process}")
            sys.exit(1)
        run_ai_pipeline(args.process, args.provider, args.model, args.whisper_model)
        return

    url = args.url or ask_url()

    print(f"\nBuscando informações do vídeo...")

    try:
        info = get_video_info(url)
    except yt_dlp.utils.DownloadError as e:
        print(f"\nErro ao acessar o vídeo: {e}")
        sys.exit(1)

    print_info(info)

    if args.info:
        return

    mode = "MP3 (apenas áudio)" if args.audio else f"MP4 ({args.quality})"
    print(f"\nIniciando download — formato: {mode}")
    print(f"Destino: {args.output}\n")

    try:
        if args.audio:
            title, filepath = download_audio(url, output_dir=args.output)
        else:
            title, filepath = download_video(url, output_dir=args.output, quality=args.quality)
    except yt_dlp.utils.DownloadError as e:
        print(f"\nErro durante o download: {e}")
        sys.exit(1)

    print(f'\nArquivo salvo em: {args.output}/')

    if args.transcribe:
        run_ai_pipeline(filepath, args.provider, args.model, args.whisper_model)


if __name__ == "__main__":
    main()
