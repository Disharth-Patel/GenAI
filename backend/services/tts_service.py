import os
import logging
from typing import Dict, Any

logger = logging.getLogger("tts_service")

# Recommended standard voice locales for target languages
VOICE_MAPPINGS = {
    "en": {"lang": "en-IN", "alt": "en-US", "name": "English (India)"},
    "hi": {"lang": "hi-IN", "alt": "hi", "name": "Hindi (India)"},
    "mr": {"lang": "mr-IN", "alt": "mr", "name": "Marathi (India)"},
    "gu": {"lang": "gu-IN", "alt": "gu", "name": "Gujarati (India)"},
    "ta": {"lang": "ta-IN", "alt": "ta", "name": "Tamil (India)"},
    "te": {"lang": "te-IN", "alt": "te", "name": "Telugu (India)"},
    "bn": {"lang": "bn-IN", "alt": "bn", "name": "Bengali (India)"},
    "kn": {"lang": "kn-IN", "alt": "kn", "name": "Kannada (India)"},
    "ml": {"lang": "ml-IN", "alt": "ml", "name": "Malayalam (India)"},
    "pa": {"lang": "pa-IN", "alt": "pa", "name": "Punjabi (India)"},
    "hinglish": {"lang": "hi-IN", "alt": "en-IN", "name": "Hindi / English (India)"},
}


class TTSService:
    """Provider-agnostic Text-to-Speech service."""

    def __init__(self):
        self.provider = os.getenv("TTS_PROVIDER", "browser")

    def get_voice_info(self, language: str) -> Dict[str, Any]:
        """Return recommended voice parameters for the given language."""
        lang_key = language.lower()
        mapping = VOICE_MAPPINGS.get(lang_key, VOICE_MAPPINGS["en"])
        return {
            "requested_language": language,
            "target_locale": mapping["lang"],
            "fallback_locale": mapping["alt"],
            "display_name": mapping["name"],
            "provider": self.provider
        }

    def synthesize(self, text: str, language: str = "en") -> Dict[str, Any]:
        """Synthesize text into speech or metadata for frontend player."""
        if not text or not text.strip():
            raise ValueError("Text to synthesize cannot be empty.")

        voice_meta = self.get_voice_info(language)
        return {
            "status": "ready",
            "text": text,
            "voice": voice_meta,
            "provider": self.provider,
            "browser_instruction": "Use window.speechSynthesis with the indicated locale."
        }


tts_service = TTSService()
