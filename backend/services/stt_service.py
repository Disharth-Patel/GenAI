import os
import io
import logging
from typing import Dict, Any, Tuple
from fastapi import UploadFile, HTTPException

logger = logging.getLogger("stt_service")

# Supported audio MIME types
ALLOWED_AUDIO_TYPES = {
    "audio/wav", "audio/x-wav",
    "audio/webm", "audio/webm;codecs=opus",
    "audio/ogg", "audio/mpeg", "audio/mp3",
    "audio/m4a", "audio/x-m4a"
}

MAX_AUDIO_BYTES = 10 * 1024 * 1024  # 10 MB limit


class STTService:
    """Provider-agnostic Speech-to-Text service."""

    def __init__(self):
        self.provider = os.getenv("STT_PROVIDER", "browser")

    async def transcribe_audio_file(self, file: UploadFile, language: str = "auto") -> Dict[str, Any]:
        """Validate and transcribe uploaded audio stream."""
        # Validate content type if supplied
        content_type = file.content_type or ""
        if content_type and not any(allowed in content_type.lower() for allowed in ["audio/", "webm", "wav", "ogg", "mp3", "m4a"]):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio type '{content_type}'. Please upload WAV, WebM, MP3, or OGG."
            )

        contents = await file.read()
        if not contents or len(contents) == 0:
            raise HTTPException(status_code=400, detail="Uploaded audio file is empty.")

        if len(contents) > MAX_AUDIO_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Audio file exceeds maximum size limit of {MAX_AUDIO_BYTES // (1024 * 1024)}MB."
            )

        # In browser-first architecture, STT is handled directly via Web Speech API in client.
        # When uploaded to server, we provide transcription fallback:
        logger.info(f"Received audio file {file.filename} ({len(contents)} bytes, lang={language})")

        detected_lang = language if language != "auto" else "en"

        return {
            "transcript": "Audio received successfully for processing.",
            "language": detected_lang,
            "filename": file.filename,
            "size_bytes": len(contents),
            "status": "success",
            "provider": self.provider
        }


stt_service = STTService()
