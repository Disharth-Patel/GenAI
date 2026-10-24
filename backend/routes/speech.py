from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from backend.services.stt_service import stt_service
from backend.services.tts_service import tts_service

router = APIRouter(prefix="/api/speech", tags=["speech"])


class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1)
    language: Optional[str] = "en"


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
