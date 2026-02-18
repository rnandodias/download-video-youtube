#!/usr/bin/env python3
"""
YouTube Downloader — baixe vídeos ou áudio do YouTube com um único comando.

Uso básico:
    python main.py <url>

Exemplos:
    python main.py "https://youtu.be/dQw4w9WgXcQ"
    python main.py "https://youtu.be/dQw4w9WgXcQ" --quality 720p
    python main.py "https://youtu.be/dQw4w9WgXcQ" --audio
    python main.py "https://youtu.be/dQw4w9WgXcQ" --output ~/Videos
"""

import argparse
import sys

import yt_dlp

from downloader import download_audio, download_video, get_video_info

VALID_QUALITIES = ["best", "1080p", "720p", "480p", "360p"]
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


def main() -> None:
    args = parse_args()

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
            title = download_audio(url, output_dir=args.output)
        else:
            title = download_video(url, output_dir=args.output, quality=args.quality)
    except yt_dlp.utils.DownloadError as e:
        print(f"\nErro durante o download: {e}")
        sys.exit(1)

    print(f'\nArquivo salvo em: {args.output}/')


if __name__ == "__main__":
    main()
