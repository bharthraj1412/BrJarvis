# api/routes/voice.py — Voice STT & TTS Endpoints
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

router = APIRouter(tags=["Voice"])


class VoiceTTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "en-US-ChristopherNeural"


class VoiceRefineRequest(BaseModel):
    text: str
    context: Optional[str] = ""


@router.post("/api/voice/refine")
async def voice_refine_endpoint(req: VoiceRefineRequest):
    """Refine a spoken draft into one executable project instruction without running it."""
    draft = " ".join(req.text.split()).strip()
    if not draft:
        raise HTTPException(status_code=400, detail="No voice transcript supplied")
    try:
        from brjarvis.core.bootstrap import build_assistant_runtime

        runtime = build_assistant_runtime()
        profile = runtime.router.route(["fast_inference", "analysis"])
        backend = runtime.router.get_backend(profile)
        if backend is None or not hasattr(backend, "complete"):
            raise RuntimeError("No configured refinement model is available")
        system = (
            "You refine speech transcripts into concise, explicit project instructions. "
            "Correct obvious transcription errors, preserve intent, fill only harmless grammar gaps, "
            "and return only the refined instruction. Do not execute tools, browse, or add commentary."
        )
        result = backend.complete(
            messages=[{"role": "user", "content": f"Spoken draft:\n{draft}\nContext:\n{req.context or 'None'}"}],
            system=system,
            max_tokens=240,
        )
        refined = " ".join(str(result or "").split()).strip()
        if not refined or refined.upper().startswith("ERROR:"):
            raise RuntimeError("The refinement model did not return a usable instruction")
        return {"status": "success", "draft": draft, "refined": refined}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Voice refinement unavailable: {exc}")


@router.post("/api/voice/stt")

async def voice_stt_endpoint(file: UploadFile = File(...)):
    """Convert uploaded audio file to text using speech-to-text engine."""
    try:
        from brjarvis.core.paths import paths

        temp_dir = paths.TEMP_ROOT / "audio_temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        audio_path = temp_dir / (file.filename or "recording.wav")
        audio_bytes = await file.read()
        audio_path.write_bytes(audio_bytes)

        from brjarvis.voice.stt import SpeechToTextEngine

        stt_engine = SpeechToTextEngine()
        text = stt_engine.transcribe(str(audio_path))
        return {"status": "success", "text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT Error: {e}")


@router.post("/api/voice/tts")
async def voice_tts_endpoint(req: VoiceTTSRequest):
    """Synthesize speech audio from text using text-to-speech engine."""
    try:
        from brjarvis.voice.tts import TextToSpeechEngine

        tts_engine = TextToSpeechEngine()
        audio_path = tts_engine.speak_to_file(req.text)
        if audio_path and Path(audio_path).exists():
            return FileResponse(audio_path, media_type="audio/mpeg", filename="speech.mp3")
        return {"status": "success", "message": "Synthesized", "text": req.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS Error: {e}")
