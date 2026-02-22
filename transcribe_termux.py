#!/usr/bin/env python3
"""
Audio Transcription Script - Termux/Android Edition
Transcreve áudio em texto usando:
  - Google Speech Recognition (online, grátis, leve)
  - Vosk (offline, funciona sem internet)

Formatos suportados: wav, mp3, flac, ogg, m4a, mp4, webm
"""

import argparse
import sys
import os
import tempfile
from pathlib import Path

SUPPORTED_FORMATS = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".mp4", ".webm"}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Transcreve áudio em texto (otimizado para Termux/Android).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Arquivo no armazenamento interno do Android (após termux-setup-storage):
  python transcribe_termux.py ~/storage/downloads/audio.mp3

  # Usar engine offline (vosk) com modelo em português:
  python transcribe_termux.py audio.wav --engine vosk --model-path ~/vosk-model-pt

  # Salvar resultado em arquivo:
  python transcribe_termux.py audio.mp3 --output transcricao.txt

  # Especificar idioma para Google:
  python transcribe_termux.py audio.mp3 --language pt-BR
        """,
    )
    parser.add_argument(
        "audio",
        help="Caminho para o arquivo de áudio.",
    )
    parser.add_argument(
        "--engine",
        choices=["google", "vosk"],
        default="google",
        help="Engine de reconhecimento: 'google' (online) ou 'vosk' (offline). Padrão: google.",
    )
    parser.add_argument(
        "--language",
        default="pt-BR",
        help="Idioma para o Google Speech (ex: pt-BR, en-US). Padrão: pt-BR.",
    )
    parser.add_argument(
        "--model-path",
        default=None,
        help="Caminho para o modelo Vosk (obrigatório se --engine vosk).",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Arquivo de saída. Se omitido, imprime no terminal.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Exibe informações detalhadas.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Conversão de formato
# ---------------------------------------------------------------------------

def convert_to_wav(audio_path: Path, verbose: bool) -> Path:
    """Converte o áudio para WAV mono 16kHz se necessário."""
    if audio_path.suffix.lower() == ".wav":
        return audio_path

    try:
        import subprocess
        out = Path(tempfile.mktemp(suffix=".wav"))
        cmd = [
            "ffmpeg", "-y",
            "-i", str(audio_path),
            "-ar", "16000",
            "-ac", "1",
            "-f", "wav",
            str(out),
        ]
        if verbose:
            print(f"Convertendo {audio_path.name} para WAV...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("Erro ao converter com ffmpeg:", result.stderr, file=sys.stderr)
            sys.exit(1)
        if verbose:
            print("Conversão concluída.")
        return out
    except FileNotFoundError:
        print(
            "Erro: ffmpeg não encontrado.\n"
            "Instale com: pkg install ffmpeg",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Engine: Google Speech Recognition
# ---------------------------------------------------------------------------

def transcribe_google(wav_path: Path, language: str, verbose: bool) -> str:
    try:
        import speech_recognition as sr
    except ImportError:
        print(
            "Erro: biblioteca 'SpeechRecognition' não instalada.\n"
            "Instale com: pip install SpeechRecognition",
            file=sys.stderr,
        )
        sys.exit(1)

    recognizer = sr.Recognizer()

    if verbose:
        print(f"Reconhecendo com Google Speech (idioma: {language})...")

    with sr.AudioFile(str(wav_path)) as source:
        audio_data = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio_data, language=language)
        return text
    except sr.UnknownValueError:
        print("Erro: não foi possível entender o áudio.", file=sys.stderr)
        sys.exit(1)
    except sr.RequestError as e:
        print(f"Erro ao acessar a API do Google: {e}", file=sys.stderr)
        print("Verifique sua conexão com a internet.", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Engine: Vosk (offline)
# ---------------------------------------------------------------------------

def transcribe_vosk(wav_path: Path, model_path: str, verbose: bool) -> str:
    try:
        from vosk import Model, KaldiRecognizer
    except ImportError:
        print(
            "Erro: biblioteca 'vosk' não instalada.\n"
            "Instale com: pip install vosk",
            file=sys.stderr,
        )
        sys.exit(1)

    import wave
    import json

    if not model_path or not Path(model_path).exists():
        print(
            "Erro: caminho do modelo Vosk não encontrado.\n"
            "Baixe um modelo em: https://alphacephei.com/vosk/models\n"
            "Para português: vosk-model-small-pt-0.3\n"
            "Exemplo: python transcribe_termux.py audio.wav --engine vosk --model-path ~/vosk-model-small-pt-0.3",
            file=sys.stderr,
        )
        sys.exit(1)

    if verbose:
        print(f"Carregando modelo Vosk de: {model_path}")

    model = Model(model_path)

    with wave.open(str(wav_path), "rb") as wf:
        sample_rate = wf.getframerate()
        rec = KaldiRecognizer(model, sample_rate)
        rec.SetWords(True)

        results = []
        while True:
            data = wf.readframes(4000)
            if not data:
                break
            if rec.AcceptWaveform(data):
                part = json.loads(rec.Result())
                results.append(part.get("text", ""))

        final = json.loads(rec.FinalResult())
        results.append(final.get("text", ""))

    return " ".join(r for r in results if r).strip()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def validate_audio(path: str) -> Path:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        print(f"Erro: arquivo não encontrado: '{path}'", file=sys.stderr)
        sys.exit(1)
    if p.suffix.lower() not in SUPPORTED_FORMATS:
        print(
            f"Erro: formato '{p.suffix}' não suportado.\n"
            f"Formatos aceitos: {', '.join(sorted(SUPPORTED_FORMATS))}",
            file=sys.stderr,
        )
        sys.exit(1)
    return p


def main():
    args = parse_args()

    audio_path = validate_audio(args.audio)

    if args.verbose:
        print(f"Arquivo: {audio_path}")

    # Converte para WAV se necessário
    wav_path = convert_to_wav(audio_path, args.verbose)
    converted = wav_path != audio_path  # será deletado ao final

    try:
        if args.engine == "google":
            text = transcribe_google(wav_path, args.language, args.verbose)
        else:
            text = transcribe_vosk(wav_path, args.model_path, args.verbose)
    finally:
        if converted and wav_path.exists():
            wav_path.unlink()

    if not text:
        print("Aviso: transcrição vazia.", file=sys.stderr)
        sys.exit(1)

    if args.output:
        out = Path(args.output)
        out.write_text(text, encoding="utf-8")
        print(f"Transcrição salva em: {out.resolve()}")
    else:
        print("\n--- Transcrição ---")
        print(text)
        print("-------------------")


if __name__ == "__main__":
    main()
