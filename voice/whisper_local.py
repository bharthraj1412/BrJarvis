# voice/whisper_local.py — JARVIS MK37 Local Whisper STT Engine
"""
Offline speech-to-text using OpenAI Whisper running locally.
Supports faster-whisper (preferred) or openai-whisper as backends.
No API calls — everything runs on the local machine.
"""
from __future__ import annotations

import io
import os
import tempfile
import traceback
from pathlib import Path


# ── Configuration ─────────────────────────────────────────────────────────────

WHISPER_MODEL = os.environ.get("JARVIS_WHISPER_MODEL", "base")
# Options: tiny, base, small, medium, large-v3
# Larger = more accurate but slower; base is a good balance

_whisper_engine = None
_engine_type = None  # "faster" or "openai"


def _get_engine():
    """Lazy-load the Whisper engine. Tries faster-whisper first, then openai-whisper."""
    global _whisper_engine, _engine_type

    if _whisper_engine is not None:
        return _whisper_engine, _engine_type

    model_name = WHISPER_MODEL

    # Try faster-whisper first (much faster with CTranslate2)
    try:
        from faster_whisper import WhisperModel
        device = "cuda" if _cuda_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        print(f"[WhisperLocal] Loading faster-whisper model '{model_name}' on {device}...")
        _whisper_engine = WhisperModel(model_name, device=device, compute_type=compute_type)
        _engine_type = "faster"
        print(f"[WhisperLocal] ✓ faster-whisper '{model_name}' ready ({device})")
        return _whisper_engine, _engine_type
    except ImportError:
        pass
    except Exception as e:
        print(f"[WhisperLocal] faster-whisper failed: {e}")

    # Fallback to openai-whisper
    try:
        import whisper
        device = "cuda" if _cuda_available() else "cpu"
        print(f"[WhisperLocal] Loading openai-whisper model '{model_name}' on {device}...")
        _whisper_engine = whisper.load_model(model_name, device=device)
        _engine_type = "openai"
        print(f"[WhisperLocal] ✓ openai-whisper '{model_name}' ready ({device})")
        return _whisper_engine, _engine_type
    except ImportError:
        pass
    except Exception as e:
        print(f"[WhisperLocal] openai-whisper failed: {e}")

    return None, None


def _cuda_available() -> bool:
    """Check if CUDA is available."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


def is_available() -> bool:
    """Check if local Whisper is available (either faster-whisper or openai-whisper installed)."""
    try:
        from faster_whisper import WhisperModel
        return True
    except ImportError:
        pass
    try:
        import whisper
        return True
    except ImportError:
        pass
    return False


def transcribe(audio_bytes: bytes, language: str = "en", detect_language: bool = False) -> str:
    """
    Transcribe audio bytes using local Whisper.

    Args:
        audio_bytes: Raw audio data (WAV format preferred).
        language: ISO-639-1 language code (e.g., 'en', 'hi', 'fr').
        detect_language: If True, auto-detect the language.

    Returns:
        Transcribed text string, or empty string on failure.
    """
    engine, engine_type = _get_engine()
    if engine is None:
        return ""

    # Write audio bytes to a temporary WAV file
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        if engine_type == "faster":
            return _transcribe_faster(engine, tmp_path, language, detect_language)
        elif engine_type == "openai":
            return _transcribe_openai(engine, tmp_path, language, detect_language)
        else:
            return ""
    except Exception as e:
        print(f"[WhisperLocal] Transcription error: {e}")
        traceback.print_exc()
        return ""
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


def _transcribe_faster(engine, audio_path: str, language: str, detect: bool) -> str:
    """Transcribe using faster-whisper."""
    kwargs = {"beam_size": 5, "vad_filter": True}
    if not detect and language:
        kwargs["language"] = language

    segments, info = engine.transcribe(audio_path, **kwargs)
    text_parts = []
    for segment in segments:
        text_parts.append(segment.text.strip())
    return " ".join(text_parts)


def _transcribe_openai(engine, audio_path: str, language: str, detect: bool) -> str:
    """Transcribe using openai-whisper."""
    kwargs = {"fp16": _cuda_available()}
    if not detect and language:
        kwargs["language"] = language

    result = engine.transcribe(audio_path, **kwargs)
    return result.get("text", "").strip()


def transcribe_file(file_path: str, language: str = "auto", output_format: str = "txt") -> dict:
    """
    Transcribe an audio or video file.

    Args:
        file_path: Path to the audio/video file.
        language: Language code or 'auto' for detection.
        output_format: 'txt', 'srt', 'vtt', or 'json'.

    Returns:
        dict with 'text', 'segments', 'language', 'output_path'.
    """
    engine, engine_type = _get_engine()
    if engine is None:
        return {"error": "No Whisper engine available. Install faster-whisper or openai-whisper."}

    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    # For video files, extract audio first
    video_exts = {".mp4", ".mkv", ".avi", ".webm", ".mov", ".flv", ".wmv"}
    audio_path = str(path)

    if path.suffix.lower() in video_exts:
        audio_path = _extract_audio(str(path))
        if not audio_path:
            return {"error": "Failed to extract audio from video. Is ffmpeg installed?"}

    try:
        detect = language == "auto"
        lang = None if detect else language

        if engine_type == "faster":
            segments_data, info = engine.transcribe(
                audio_path,
                beam_size=5,
                vad_filter=True,
                language=lang if not detect else None,
                word_timestamps=True,
            )
            segments = []
            full_text = []
            for seg in segments_data:
                segments.append({
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text.strip(),
                })
                full_text.append(seg.text.strip())

            detected_lang = getattr(info, "language", language)
        else:
            result = engine.transcribe(
                audio_path,
                language=lang if not detect else None,
                fp16=_cuda_available(),
            )
            segments = []
            for seg in result.get("segments", []):
                segments.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"].strip(),
                })
            full_text = [result.get("text", "").strip()]
            detected_lang = result.get("language", language)

        text = " ".join(full_text)

        # Generate output file
        output_path = str(path.with_suffix(f".{output_format}"))
        if output_format == "txt":
            Path(output_path).write_text(text, encoding="utf-8")
        elif output_format == "srt":
            _write_srt(segments, output_path)
        elif output_format == "vtt":
            _write_vtt(segments, output_path)
        elif output_format == "json":
            import json
            Path(output_path).write_text(
                json.dumps({"text": text, "segments": segments, "language": detected_lang}, indent=2),
                encoding="utf-8",
            )

        return {
            "text": text,
            "segments": segments,
            "language": detected_lang,
            "output_path": output_path,
            "segment_count": len(segments),
        }

    except Exception as e:
        return {"error": f"Transcription failed: {e}"}
    finally:
        # Clean up extracted audio
        if path.suffix.lower() in video_exts and audio_path != str(path):
            try:
                os.unlink(audio_path)
            except Exception:
                pass


def _extract_audio(video_path: str) -> str | None:
    """Extract audio from video file using ffmpeg."""
    import subprocess
    output_path = tempfile.mktemp(suffix=".wav")
    try:
        subprocess.run(
            ["ffmpeg", "-i", video_path, "-vn", "-acodec", "pcm_s16le",
             "-ar", "16000", "-ac", "1", output_path, "-y"],
            capture_output=True, timeout=300,
        )
        if Path(output_path).exists() and Path(output_path).stat().st_size > 0:
            return output_path
        return None
    except Exception:
        return None


def _format_timestamp(seconds: float, fmt: str = "srt") -> str:
    """Format seconds into SRT or VTT timestamp."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    sep = "," if fmt == "srt" else "."
    return f"{hrs:02d}:{mins:02d}:{secs:02d}{sep}{ms:03d}"


def _write_srt(segments: list[dict], output_path: str):
    """Write segments as SRT subtitle file."""
    lines = []
    for i, seg in enumerate(segments, 1):
        start = _format_timestamp(seg["start"], "srt")
        end = _format_timestamp(seg["end"], "srt")
        lines.append(f"{i}\n{start} --> {end}\n{seg['text']}\n")
    Path(output_path).write_text("\n".join(lines), encoding="utf-8")


def _write_vtt(segments: list[dict], output_path: str):
    """Write segments as WebVTT subtitle file."""
    lines = ["WEBVTT\n"]
    for seg in segments:
        start = _format_timestamp(seg["start"], "vtt")
        end = _format_timestamp(seg["end"], "vtt")
        lines.append(f"{start} --> {end}\n{seg['text']}\n")
    Path(output_path).write_text("\n".join(lines), encoding="utf-8")
