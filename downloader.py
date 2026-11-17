import os
from typing import Tuple

import yt_dlp


QUALITY_FORMATS = {
    "best":  "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best[height<=1080]",
    "720p":  "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]",
    "480p":  "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best[height<=480]",
    "360p":  "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best[height<=360]",
}


def _build_progress_hook():
    last_pct = [-1]

    def hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            speed = d.get("speed")
            eta = d.get("eta")

            if total:
                pct = int(downloaded / total * 100)
                if pct != last_pct[0]:
                    last_pct[0] = pct
                    bar = "#" * (pct // 5) + "-" * (20 - pct // 5)
                    speed_str = f"{speed / 1024:.1f} KB/s" if speed else "-- KB/s"
                    eta_str = f"{eta}s" if eta else "--s"
                    print(f"\r  [{bar}] {pct:3d}%  {speed_str}  ETA: {eta_str}   ", end="", flush=True)
            else:
                mb = downloaded / (1024 * 1024)
                print(f"\r  Baixando... {mb:.1f} MB", end="", flush=True)

        elif d["status"] == "finished":
            print(f"\r  [{'#' * 20}] 100%  Concluído!{' ' * 20}")

        elif d["status"] == "error":
            print("\n  Erro durante o download.")

    return hook


def _get_filepath(info: dict, fallback: str) -> str:
    """
    Extrai o caminho real do arquivo a partir do info dict do yt-dlp.
    Usa requested_downloads[0]['filepath'], que contém o caminho exato
    após sanitização de caracteres especiais (ex: '/' vira '⧸').
    """
    requested = info.get("requested_downloads") or []
    if requested and requested[0].get("filepath"):
        return requested[0]["filepath"]
    return fallback


def get_video_info(url: str) -> dict:
    """Retorna metadados do vídeo sem fazer download."""
    ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return {
        "title": info.get("title", "Desconhecido"),
        "duration": info.get("duration_string", "?"),
        "uploader": info.get("uploader", "?"),
        "view_count": info.get("view_count", 0),
    }


def download_video(
    url: str, output_dir: str = "./downloads", quality: str = "best"
) -> Tuple[str, str]:
    """
    Faz o download de um vídeo do YouTube em formato MP4.

    Returns:
        Tupla (título, caminho_completo_do_arquivo).
    """
    os.makedirs(output_dir, exist_ok=True)

    format_str = QUALITY_FORMATS.get(quality, QUALITY_FORMATS["best"])

    ydl_opts = {
        "format": format_str,
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "merge_output_format": "mp4",
        "progress_hooks": [_build_progress_hook()],
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    title = info.get("title", "Desconhecido")
    filepath = _get_filepath(info, os.path.join(output_dir, f"{title}.mp4"))

    return title, filepath


def download_audio(url: str, output_dir: str = "./downloads") -> Tuple[str, str]:
    """
    Faz o download apenas do áudio do vídeo e converte para MP3.

    Returns:
        Tupla (título, caminho_completo_do_arquivo).

    Nota: requer ffmpeg instalado no sistema.
    """
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "progress_hooks": [_build_progress_hook()],
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    title = info.get("title", "Desconhecido")
    filepath = _get_filepath(info, os.path.join(output_dir, f"{title}.mp3"))

    return title, filepath
