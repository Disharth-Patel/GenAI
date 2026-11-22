import re
import urllib.request
import urllib.parse
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Optional

from backend.services.stt_service import stt_service
from backend.services.tts_service import tts_service

router = APIRouter(prefix="/api/speech", tags=["speech"])


class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1)
    language: Optional[str] = "en"


@router.get("/stream")
@router.get("/stream/")
def stream_speech_audio(text: str = Query(..., min_length=1), language: Optional[str] = "mr"):
    """
    Stream native browser-based speaking audio for any text in Marathi, Gujarati, Hindi, English, etc.
    Guarantees natural pronunciation on all systems even when client PC lacks local Indic SAPI voices.
    """
    clean_text = re.sub(r"\[.*?\]\(.*?\)|\*\*|_|#|`|https?://\S+", " ", text)
    clean_text = re.sub(r"\s+", " ", clean_text).strip()
    if not clean_text:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    # Slice chunk to safe length for clean audio streaming
    chunk = clean_text[:240]
    lang_code = (language or "en").lower()
    tl_map = {
        "mr": "mr",
        "gu": "gu",
        "hi": "hi",
        "ta": "ta",
        "te": "te",
        "bn": "bn",
        "kn": "kn",
        "ml": "ml",
        "pa": "pa",
        "hinglish": "hi",
        "gujlish": "gu",
        "en": "en"
    }
    tl = tl_map.get(lang_code, "en")

    encoded_q = urllib.parse.quote(chunk)
    url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl={tl}&client=tw-ob&q={encoded_q}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            audio_bytes = resp.read()
            return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"TTS streaming error: {str(exc)}")


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Form("auto")
):
    """
    Transcribe uploaded audio file and return text transcript with detected language.
    """
    try:
        result = await stt_service.transcribe_audio_file(file=file, language=language)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio processing error: {str(e)}")


@router.post("/synthesize")
def synthesize_speech(req: SynthesizeRequest):
    """
    Generate speech synthesis metadata and voice locale configuration for speech output.
    """
    try:
        return tts_service.synthesize(text=req.text, language=req.language or "en")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synthesis error: {str(e)}")
