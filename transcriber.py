import os

import whisper


def transcribe(file_path: str, model_size: str = "large") -> dict:
    """
    Transcreve um arquivo de áudio ou vídeo usando o Whisper.

    Args:
        file_path:   Caminho para o arquivo (.mp3, .mp4, etc.).
        model_size:  Tamanho do modelo Whisper (tiny, base, small, medium, large).

    Returns:
        dict com 'text' (transcrição) e 'language' (código do idioma detectado).
    """
    print(f"  Carregando modelo Whisper '{model_size}'...")
    model = whisper.load_model(model_size)

    print(f"  Transcrevendo '{os.path.basename(file_path)}'...")
    result = model.transcribe(file_path)

    return {
        "text": result["text"].strip(),
        "language": result["language"],
    }
