import json
import os
import shutil
import subprocess
from typing import Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import yt_dlp


QUALITY_FORMATS = {
    "best":  "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/bestvideo+bestaudio/best",
    "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
    "720p":  "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/bestvideo[height<=720]+bestaudio/best[height<=720]/best",
    "480p":  "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/bestvideo[height<=480]+bestaudio/best[height<=480]/best",
    "360p":  "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/bestvideo[height<=360]+bestaudio/best[height<=360]/best",
}

# Parâmetros de rastreamento adicionados pelos botões de "compartilhar".
# Não afetam qual vídeo é baixado e identificam quem compartilhou o link.
_TRACKING_PARAMS = {"si", "srtk", "igsh", "igshid", "feature", "fbclid"}

# O título vem antes; o ID evita que posts com o mesmo título
# (ex.: "Video by usuario" no Instagram) sobrescrevam uns aos outros.
_OUTTMPL = "%(title).150B [%(id)s].%(ext)s"


def clean_url(url: str) -> str:
    """Remove parâmetros de rastreamento (utm_*, si, srtk, igsh...) do link."""
    parts = urlsplit(url.strip())
    query = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k not in _TRACKING_PARAMS and not k.startswith("utm_")
    ]
    return urlunsplit(parts._replace(query=urlencode(query)))


def _base_opts(cookies: Optional[str]) -> dict:
    opts = {"quiet": True, "no_warnings": True}
    if cookies:
        opts["cookiefile"] = cookies
    return opts


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


def get_video_info(url: str, cookies: Optional[str] = None) -> dict:
    """Retorna metadados do vídeo sem fazer download."""
    ydl_opts = {**_base_opts(cookies), "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return {
        "title": info.get("title", "Desconhecido"),
        "duration": info.get("duration_string", "?"),
        "uploader": info.get("uploader") or info.get("channel") or "?",
        "view_count": info.get("view_count", 0),
        "platform": info.get("extractor_key", "?"),
    }


def download_video(
    url: str,
    output_dir: str = "./downloads",
    quality: str = "best",
    cookies: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Faz o download de um vídeo (YouTube, Instagram...) em formato MP4.

    Returns:
        Tupla (título, caminho_completo_do_arquivo).
    """
    os.makedirs(output_dir, exist_ok=True)

    format_str = QUALITY_FORMATS.get(quality, QUALITY_FORMATS["best"])

    ydl_opts = {
        **_base_opts(cookies),
        "format": format_str,
        "outtmpl": os.path.join(output_dir, _OUTTMPL),
        "merge_output_format": "mp4",
        "progress_hooks": [_build_progress_hook()],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    title = info.get("title", "Desconhecido")
    filepath = _get_filepath(info, os.path.join(output_dir, f"{title}.mp4"))

    return title, filepath


def _probe_streams(filepath: str) -> dict:
    """Retorna o primeiro stream de vídeo e de áudio do arquivo, via ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "stream=codec_type,codec_name,pix_fmt",
            "-of", "json", filepath,
        ],
        capture_output=True, text=True, check=True,
    )
    streams = {}
    for s in json.loads(result.stdout).get("streams", []):
        if s.get("codec_type") in ("video", "audio"):
            streams.setdefault(s["codec_type"], s)
    return streams


def make_compatible(filepath: str) -> Tuple[str, bool]:
    """
    Garante um MP4 com vídeo H.264 (yuv420p) e áudio AAC — formato aceito
    por WhatsApp, Teams, iPhone, editores de vídeo etc.

    Só recodifica o stream que não for compatível; o que já for é copiado
    sem perda. O arquivo convertido substitui o original.

    Returns:
        Tupla (caminho_final, houve_conversao).
    """
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("ffmpeg/ffprobe não encontrados no PATH")

    streams = _probe_streams(filepath)
    video, audio = streams.get("video"), streams.get("audio")
    video_ok = video is None or (
        video.get("codec_name") == "h264" and video.get("pix_fmt") == "yuv420p"
    )
    audio_ok = audio is None or audio.get("codec_name") == "aac"
    base = os.path.splitext(filepath)[0]
    final = f"{base}.mp4"

    if video_ok and audio_ok and filepath == final:
        return filepath, False

    tmp = f"{base}.compat.tmp.mp4"
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", filepath]
    cmd += ["-c:v", "copy"] if video_ok else [
        "-c:v", "libx264", "-preset", "slow", "-crf", "22",
        "-pix_fmt", "yuv420p", "-profile:v", "high",
    ]
    cmd += ["-c:a", "copy"] if audio_ok else ["-c:a", "aac", "-b:a", "128k"]
    cmd += ["-movflags", "+faststart", tmp]

    try:
        subprocess.run(cmd, check=True)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise

    os.replace(tmp, final)
    if filepath != final:
        os.remove(filepath)
    return final, True


def download_audio(
    url: str, output_dir: str = "./downloads", cookies: Optional[str] = None
) -> Tuple[str, str]:
    """
    Faz o download apenas do áudio do vídeo e converte para MP3.

    Returns:
        Tupla (título, caminho_completo_do_arquivo).

    Nota: requer ffmpeg instalado no sistema.
    """
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        **_base_opts(cookies),
        "format": "bestaudio/best",
        "outtmpl": os.path.join(output_dir, _OUTTMPL),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "progress_hooks": [_build_progress_hook()],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    title = info.get("title", "Desconhecido")
    filepath = _get_filepath(info, os.path.join(output_dir, f"{title}.mp3"))

    return title, filepath
