#!/usr/bin/env python3
"""
Audio Transcription Script
Transcribes audio files to text using OpenAI Whisper.

Supported formats: mp3, mp4, wav, flac, ogg, m4a, webm
"""

import argparse
import sys
import time
from pathlib import Path


SUPPORTED_FORMATS = {".mp3", ".mp4", ".wav", ".flac", ".ogg", ".m4a", ".webm"}

WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Transcreve áudio em texto usando OpenAI Whisper.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python transcribe.py audio.mp3
  python transcribe.py audio.wav --model medium --language pt
  python transcribe.py audio.flac --output resultado.txt --model large
  python transcribe.py audio.mp4 --language en --model small
        """,
    )
    parser.add_argument(
        "audio",
        help="Caminho para o arquivo de áudio a ser transcrito.",
    )
    parser.add_argument(
        "--model",
        choices=WHISPER_MODELS,
        default="base",
        help=(
            "Modelo Whisper a usar. Modelos maiores são mais precisos, porém mais lentos. "
            "Padrão: base. Opções: tiny, base, small, medium, large."
        ),
    )
    parser.add_argument(
        "--language",
        default=None,
        help=(
            "Código do idioma do áudio (ex: 'pt' para português, 'en' para inglês). "
            "Se omitido, o Whisper detecta automaticamente."
        ),
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help=(
            "Arquivo de saída para salvar a transcrição. "
            "Se omitido, imprime no terminal."
        ),
    )
    parser.add_argument(
        "--task",
        choices=["transcribe", "translate"],
        default="transcribe",
        help=(
            "Tarefa a executar: 'transcribe' (transcreve no idioma original) "
            "ou 'translate' (traduz para inglês). Padrão: transcribe."
        ),
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Exibe informações detalhadas durante o processo.",
    )
    return parser.parse_args()


def validate_audio_file(path: str) -> Path:
    audio_path = Path(path)

    if not audio_path.exists():
        print(f"Erro: arquivo não encontrado: '{path}'", file=sys.stderr)
        sys.exit(1)

    if not audio_path.is_file():
        print(f"Erro: '{path}' não é um arquivo válido.", file=sys.stderr)
        sys.exit(1)

    if audio_path.suffix.lower() not in SUPPORTED_FORMATS:
        print(
            f"Erro: formato '{audio_path.suffix}' não suportado.\n"
            f"Formatos aceitos: {', '.join(sorted(SUPPORTED_FORMATS))}",
            file=sys.stderr,
        )
        sys.exit(1)

    return audio_path


def load_whisper(model_name: str, verbose: bool):
    try:
        import whisper
    except ImportError:
        print(
            "Erro: pacote 'openai-whisper' não instalado.\n"
            "Instale com: pip install openai-whisper",
            file=sys.stderr,
        )
        sys.exit(1)

    if verbose:
        print(f"Carregando modelo '{model_name}'...")

    model = whisper.load_model(model_name)

    if verbose:
        print("Modelo carregado com sucesso.")

    return model


def transcribe(model, audio_path: Path, language: str, task: str, verbose: bool) -> dict:
    if verbose:
        print(f"Transcrevendo: {audio_path.name}")
        print(f"  Tarefa   : {task}")
        print(f"  Idioma   : {language if language else 'detecção automática'}")

    start = time.time()

    options = {"task": task}
    if language:
        options["language"] = language

    result = model.transcribe(str(audio_path), **options)

    elapsed = time.time() - start
    if verbose:
        detected = result.get("language", "desconhecido")
        print(f"  Idioma detectado: {detected}")
        print(f"  Duração do processamento: {elapsed:.1f}s")

    return result


def save_output(text: str, output_path: str, verbose: bool):
    out = Path(output_path)
    out.write_text(text, encoding="utf-8")
    if verbose:
        print(f"Transcrição salva em: {out.resolve()}")


def main():
    args = parse_args()

    audio_path = validate_audio_file(args.audio)
    model = load_whisper(args.model, args.verbose)
    result = transcribe(model, audio_path, args.language, args.task, args.verbose)

    text = result["text"].strip()

    if args.output:
        save_output(text, args.output, args.verbose)
    else:
        print("\n--- Transcrição ---")
        print(text)
        print("-------------------")


if __name__ == "__main__":
    main()
