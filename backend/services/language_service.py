"""
Centralized Multilingual Language Detection and Management Service.
Provides native script detection, Romanized/transliterated dialect detection (Hinglish, Gujlish, Marathlish),
code-switching handling, conversational greeting recognition, and speech locale resolution.
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger("language_service")


@dataclass
class LanguageProfile:
    code: str
    name: str
    native_name: str
    script: str
    speech_locale: str
    fallback_locale: str
    tts_voice_names: List[str]
    has_text_input: bool = True
    has_text_generation: bool = True
    has_stt: bool = True
    has_tts: bool = True


# Comprehensive Inventory of Supported Languages
SUPPORTED_LANGUAGES: Dict[str, LanguageProfile] = {
    "en": LanguageProfile(
        code="en",
        name="English",
        native_name="English",
        script="Latin",
        speech_locale="en-IN",
        fallback_locale="en-US",
        tts_voice_names=["English India", "Ravi", "Heera", "en-IN", "en_IN", "en-US"]
    ),
    "mr": LanguageProfile(
        code="mr",
        name="Marathi",
        native_name="मराठी",
        script="Devanagari",
        speech_locale="mr-IN",
        fallback_locale="hi-IN",
        tts_voice_names=["Marathi India", "Aarohi", "mr-IN", "mr_IN", "mr"]
    ),
    "hi": LanguageProfile(
        code="hi",
        name="Hindi",
        native_name="हिन्दी",
        script="Devanagari",
        speech_locale="hi-IN",
        fallback_locale="en-IN",
        tts_voice_names=["Hindi India", "Madhur", "Swara", "hi-IN", "hi_IN", "hi"]
    ),
    "gu": LanguageProfile(
        code="gu",
        name="Gujarati",
        native_name="ગુજરાતી",
        script="Gujarati",
        speech_locale="gu-IN",
        fallback_locale="hi-IN",
        tts_voice_names=["Gujarati India", "Dhwani", "Niranjan", "gu-IN", "gu_IN", "gu"]
    ),
    "ta": LanguageProfile(
        code="ta",
        name="Tamil",
        native_name="தமிழ்",
        script="Tamil",
        speech_locale="ta-IN",
        fallback_locale="en-IN",
        tts_voice_names=["Tamil India", "Valluvar", "Iniyavan", "ta-IN", "ta_IN", "ta"]
    ),
    "te": LanguageProfile(
        code="te",
        name="Telugu",
        native_name="తెలుగు",
        script="Telugu",
        speech_locale="te-IN",
        fallback_locale="en-IN",
        tts_voice_names=["Telugu India", "Mohan", "Shruti", "te-IN", "te_IN", "te"]
    ),
    "bn": LanguageProfile(
        code="bn",
        name="Bengali",
        native_name="বাংলা",
        script="Bengali",
        speech_locale="bn-IN",
        fallback_locale="hi-IN",
        tts_voice_names=["Bengali India", "Bashkar", "Tanishaa", "bn-IN", "bn_IN", "bn"]
    ),
    "kn": LanguageProfile(
        code="kn",
        name="Kannada",
        native_name="ಕನ್ನಡ",
        script="Kannada",
        speech_locale="kn-IN",
        fallback_locale="en-IN",
        tts_voice_names=["Kannada India", "Gagan", "Sapna", "kn-IN", "kn_IN", "kn"]
    ),
    "ml": LanguageProfile(
        code="ml",
        name="Malayalam",
        native_name="മലയാളം",
        script="Malayalam",
        speech_locale="ml-IN",
        fallback_locale="en-IN",
        tts_voice_names=["Malayalam India", "Midhun", "Sobhana", "ml-IN", "ml_IN", "ml"]
    ),
    "pa": LanguageProfile(
        code="pa",
        name="Punjabi",
        native_name="ਪੰਜਾਬੀ",
        script="Gurmukhi",
        speech_locale="pa-IN",
        fallback_locale="hi-IN",
        tts_voice_names=["Punjabi India", "pa-IN", "pa_IN", "pa"]
    ),
    "hinglish": LanguageProfile(
        code="hinglish",
        name="Hinglish",
        native_name="Hinglish (Hindi in Latin script)",
        script="Latin",
        speech_locale="hi-IN",
        fallback_locale="en-IN",
        tts_voice_names=["Hindi India", "English India", "hi-IN", "en-IN"]
    ),
    "gujlish": LanguageProfile(
        code="gujlish",
        name="Gujlish",
        native_name="Gujlish (Gujarati in Latin script)",
        script="Latin",
        speech_locale="gu-IN",
        fallback_locale="en-IN",
        tts_voice_names=["Gujarati India", "English India", "gu-IN", "en-IN"]
    ),
}

# Lexical markers for Devanagari disambiguation
MARATHI_SPECIFIC_MARKERS = {
    "आहे", "आहेत", "नाही", "नाहीत", "विद्यार्थ्यांसाठी", "कागदपत्रे",
    "कसा", "कशी", "कोणती", "कोणता", "कोणते", "करावा", "करावी", "मिळेल",
    "मिळतो", "मिळते", "मिळणार", "शिष्यवृत्ती", "वसतिगृह", "शाळा", "महाडीबीटी",
    "मिळू", "शकते", "सांग", "सांगा", "माहिती", "काय", "लागेल", "पाहिजे",
    "च्या", "मध्ये", "करायचा", "करायचे", "द्या", "भत्ता", "बद्दल", "कधी",
    "कुठे", "अर्ज", "सादर", "करावे", "होईल", "येथे", "शासन", "निर्णय",
    "मदत", "तपासणी", "पात्र", "अपात्र", "योजनेचा", "लाभ", "घ्यावा",
    "कसा", "कशी", "कसे"
}

HINDI_SPECIFIC_MARKERS = {
    "है", "हैं", "नहीं", "छात्र", "छात्रों", "के", "लिए", "आवेदन", "दस्तावेज़",
    "कैसे", "मिलेगा", "मिलता", "मिलती", "क्या", "छात्रवृत्ति", "हॉस्टल", "चाहिए",
    "सकते", "सकती", "बताएं", "बताओ", "बताइए", "जानकारी", "प्रक्रिया", "करना",
    "होगी", "होगा", "दीजिए", "विवरण", "शुरू", "अंतिम", "में", "कितना", "कितनी",
    "का", "की", "को", "से", "पर", "होता", "होती", "रहे", "रहा", "रही", "मुझे",
    "मेरा", "मेरी", "हमारा", "कहाँ", "कब", "कौन", "कौनसा", "कौनसी", "दें"
}

# Gujarati lexical words in native script
GUJARATI_SPECIFIC_MARKERS = {
    "છે", "છો", "નથી", "શિક્ષણ", "વિદ્યાર્થી", "યોજના", "શિષ્યવૃત્તિ", "માહિતી",
    "કેમ", "શું", "જોઈએ", "કરવું", "માટે", "તમે", "હું", "આપો", "આપશો", "વિશે",
    "કેટલી", "કેટલા", "ક્યારે", "ક્યાં", "હોસ્ટેલ", "અરજી", "જરૂરી", "કાગળો",
    "લાયકાત", "મળશે", "મળે", "આવક", "મર્યાદા", "સાથે", "વાતચીત", "પ્રશ્નો"
}

# Romanized / Transliterated Keywords
GUJLISH_PATTERNS = {
    "kem", "cho", "chho", "chhe", "su", "shu", "nathi", "joiye", "karvu",
    "karvanu", "mate", "aavse", "tamne", "tamaru", "tamari", "vicharo",
    "karshe", "shikshan", "aapo", "aapsho", "bhai", "ben", "ketla", "ketli",
    "kyare", "kya", "koni", "badha", "badhi", "vichar", "maru", "mari",
    "mare", "tame", "hu", "tane", "mane", "khabar", "haji", "pachhi"
}

HINGLISH_PATTERNS = {
    "kya", "hai", "kaise", "milega", "chahiye", "batao", "bataiye", "yojana",
    "shiksha", "vidyarthi", "form", "bharna", "kab", "se", "ko", "mein",
    "me", "par", "aur", "nahi", "ho", "sakte", "sakti", "kar", "rahe", "raha",
    "mujhe", "mera", "meri", "unka", "iska", "iske", "iski", "karein", "hoga",
    "hogi", "wala", "wali", "kitna", "kitni", "paisa", "paise", "kahan", "kaun",
    "kaunsi", "milta", "milti", "shart", "patrata", "kagaz", "dastavez", "bataye",
    "chhatravritti", "madad", "dijiye", "shuru", "khatam", "bhi", "lagta", "lagti",
    "sakta", "sakti", "dena", "le", "sakenge", "baare", "bare"
}

MARATHLISH_PATTERNS = {
    "kasa", "kashi", "kase", "ahes", "ahe", "ahet", "nahi", "shishyavrutti",
    "vasatigruh", "sathi", "karave", "lagel", "milnar", "mahiti", "konta",
    "konte", "dya", "kuthe", "kadhi", "pahije", "kay", "karaycha", "kiti",
    "mula", "muli", "mulanna", "shikshan", "baddal"
}

COMMON_ENGLISH_WORDS = {
    "what", "is", "the", "how", "can", "i", "apply", "for", "scholarship",
    "which", "documents", "eligibility", "where", "tell", "me", "about",
    "college", "hostel", "course", "fees", "student", "students", "income",
    "limit", "criteria", "benefits", "portal", "deadline", "when", "who", "why",
    "hello", "hi", "hey", "good", "morning", "afternoon", "evening", "thanks", "thank",
    "you", "admission", "process", "university", "department", "details", "information"
}

# Natural Conversational Greetings across languages
CONVERSATIONAL_GREETINGS = {
    # Gujarati greetings
    "તમે કેમ છો": ("gu", "હું મજામાં છું! તમે કેમ છો? હું તમને મહારાષ્ટ્ર ઓબીસી સ્કોલરશિપ અને શિક્ષણ યોજનાઓ વિશે શું સહાય કરી શકું?"),
    "કેમ છો": ("gu", "હું એકદમ મજામાં છું! તમે કેમ છો? આજે હું તમને કઈ શિક્ષણ કે સ્કોલરશિપ યોજના વિશે માહિતી આપું?"),
    "તમે શું કરો છો": ("gu", "હું તમારી સાથે વાતચીત કરવા અને મહારાષ્ટ્ર સરકારની શિષ્યવૃત્તિ, હોસ્ટેલ અને શિક્ષણ સહાય સંબંધિત તમારા પ્રશ્નોના જવાબ આપવા માટે અહીં છું."),
    "નમસ્તે": ("gu", "નમસ્તે! હું મહારાષ્ટ્ર ઓબીસી એજ્યુકેશન એઆઈ સહાયક છું. હું તમને કેવી રીતે મદદ કરી શકું?"),
    "નમસ્કાર": ("gu", "નમસ્કાર! આપનું સ્વાગત છે. ઓબીસી સ્કોલરશિપ કે પ્રવેશ સંબંધિત તમારો પ્રશ્ન પૂછો."),
    # Hindi greetings
    "आप कैसे हैं": ("hi", "मैं बिल्कुल ठीक हूँ! आप कैसे हैं? मैं महाराष्ट्र ओबीसी शिक्षा योजनाओं और छात्रवृत्ति के बारे में आपकी क्या सहायता कर सकता हूँ?"),
    "कैसे हो": ("hi", "मैं बहुत बढ़िया हूँ! आप कैसे हैं? आप किस योजना या छात्रवृत्ति के बारे में जानना चाहते हैं?"),
    "नमस्ते": ("hi", "नमस्ते! महाराष्ट्र ओबीसी शिक्षा एवं कल्याण एआई सहायक में आपका स्वागत है। मैं आपकी क्या मदद कर सकता हूँ?"),
    "नमस्कार": ("hi", "नमस्कार! आपका स्वागत है। आप महाराष्ट्र छात्रवृत्ति, हॉस्टल या शुल्क प्रतिपूर्ति के बारे में पूछ सकते हैं।"),
    "आप क्या कर रहे हैं": ("hi", "मैं आपकी सहायता करने और महाराष्ट्र सरकार की योजनाओं व छात्रवृत्ति से जुड़े सवालों के सटीक जवाब देने के लिए यहाँ उपस्थित हूँ।"),
    "आप क्या करते हैं": ("hi", "मैं महाराष्ट्र के ओबीसी, वीजेएनटी और एसबीसी विद्यार्थियों को शिक्षा योजनाओं, महाडीबीटी छात्रवृत्ति और हॉस्टल की जानकारी देने के लिए यहाँ हूँ।"),
    # Marathi greetings
    "तुम्ही कसे आहात": ("mr", "मी अगदी मजेत आहे! तुम्ही कसे आहात? मी तुम्हाला इतर मागास बहुजन कल्याण विभागाच्या शिष्यवृत्ती आणि शैक्षणिक योजनांबद्दल कशी मदत करू शकतो?"),
    "कसे आहात": ("mr", "मी छान आहे! तुम्ही कसे आहात? महाडीबीटी शिष्यवृत्ती, वसतिगृह किंवा इतर योजनांबद्दल आपला प्रश्न विचारा."),
    "नमस्कार": ("mr", "नमस्कार! महाराष्ट्र ओबीसी शिक्षण एआय सहाय्यकामध्ये आपले स्वागत आहे. मी आपल्याला कशी मदत करू शकतो?"),
    "तुम्ही काय करता": ("mr", "मी विद्यार्थ्यांना महाराष्ट्र शासनाच्या विविध शिष्यवृत्ती, स्वाधार योजना, वसतिगृहे आणि प्रवेश सवलतींबद्दल अचूक माहिती देण्यासाठी येथे उपलब्ध आहे."),
    # Tamil greetings
    "எப்படி இருக்கிறீர்கள்": ("ta", "நான் நலமாக இருக்கிறேன்! நீங்கள் எப்படி இருக்கிறீர்கள்? கல்வி உதவித்தொகை மற்றும் கல்வித் திட்டங்கள் குறித்து நான் உங்களுக்கு எவ்வாறு உதவ முடியும்?"),
    "வணக்கம்": ("ta", "வணக்கம்! பிற்படுத்தப்பட்டோர் கல்வி உதவித்தொகை மற்றும் கல்லூரி திட்டங்கள் குறித்து உங்கள் கேள்விகளைக் கேளுங்கள்."),
    # Telugu greetings
    "ఎలా ఉన్నారు": ("te", "నేను బాగున్నాను! మీరు ఎలా ఉన్నారు? ఒబిసి స్కాలర్‌షిప్‌లు మరియు విద్యా పథకాల గురించి మీకు ఏ సమాచారం కావాలి?"),
    "నమస్కారం": ("te", "నమస్కారం! ఒబిసి సంక్షేమ మరియు స్కాలర్‌షిప్ పథకాల గురించి మీకు ఎలా సహాయపడగలను?"),
    # Bengali greetings
    "কেমন আছেন": ("bn", "আমি ভালো আছি! আপনি কেমন আছেন? ওবিসি স্কলারশিপ এবং শিক্ষা সহায়তা প্রকল্প সম্পর্কে আমি আপনাকে কীভাবে সাহায্য করতে পারি?"),
    "নমস্কার": ("bn", "নমস্কার! স্কলারশিপ এবং শিক্ষা প্রকল্প সম্পর্কিত আপনার প্রশ্ন জিজ্ঞাসা করুন।"),
    # Punjabi greetings
    "ਕਿਵੇਂ ਹੋ": ("pa", "ਮੈਂ ਬਿਲਕੁਲ ਠੀਕ ਹਾਂ! ਤੁਸੀਂ ਕਿਵੇਂ ਹੋ? ਮੈਂ ਓਬੀਸੀ ਸਕਾਲਰਸ਼ਿਪ ਅਤੇ ਸਿੱਖਿਆ ਸਕੀਮਾਂ ਬਾਰੇ ਤੁਹਾਡੀ ਕੀ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?"),
    "ਸਤਿ ਸ਼੍ਰੀ ਅਕਾਲ": ("pa", "ਸਤਿ ਸ਼੍ਰੀ ਅਕਾਲ! ਓਬੀਸੀ ਵਜ਼ੀਫਾ ਅਤੇ ਸਿੱਖਿਆ ਯੋਜਨਾਵਾਂ ਸੰਬੰਧੀ ਆਪਣਾ ਸਵਾਲ ਪੁੱਛੋ।"),
    # English greetings
    "how are you": ("en", "I'm doing great, thank you! How are you doing today? How can I assist you with Maharashtra OBC scholarships, hostels, or education schemes?"),
    "hello": ("en", "Hello! Welcome to the Maharashtra OBC Education & Welfare AI Assistant. How can I help you today?"),
    "hi": ("en", "Hi there! Feel free to ask any question regarding scholarships, eligibility, hostel facilities, or the MahaDBT portal."),
    "hey": ("en", "Hey! How can I assist you with Maharashtra education schemes or scholarships today?"),
    "what do you do": ("en", "I am an AI assistant dedicated to helping students explore and apply for scholarships, hostel facilities, fee reimbursements, and education schemes under Maharashtra Bahujan Kalyan Department."),
}


@dataclass
class DetectionResult:
    language_code: str
    language_name: str
    native_name: str
    script: str
    confidence: float
    is_code_switched: bool
    is_transliterated: bool
    speech_locale: str
    conversational_reply: Optional[str] = None


# Alias for compatibility
LanguageDetectionResult = DetectionResult


LANGUAGE_NAMES = {k: f"{v.name} ({v.native_name})" for k, v in SUPPORTED_LANGUAGES.items()}
LANGUAGE_NAMES["unknown"] = "Clarification Required"


class CentralLanguageService:
    """
    Centralized intelligent language detection, switching, and speech configuration service.
    Handles Indic scripts, transliterated Roman dialects, code-switching, and natural greetings.
    """

    LANGUAGE_NAMES = LANGUAGE_NAMES

    def __init__(self):
        self.languages = SUPPORTED_LANGUAGES
        self.LANGUAGE_NAMES = LANGUAGE_NAMES

    def get_supported_inventory(self) -> List[Dict[str, Any]]:
        """Return the complete inventory of supported languages and their capabilities."""
        return [asdict(p) for p in self.languages.values()]

    def detect_language(self, text: str, fallback: str = "en") -> DetectionResult:
        """
        Intelligently detect the language and script of any input message.
        Handles typed messages, transcribed voice, mixed-language queries, and transliterations.
        """
        raw_text = (text or "").strip()
        if not raw_text:
            profile = self.languages.get(fallback, self.languages["en"])
            return DetectionResult(
                language_code=profile.code,
                language_name=profile.name,
                native_name=profile.native_name,
                script=profile.script,
                confidence=1.0,
                is_code_switched=False,
                is_transliterated=False,
                speech_locale=profile.speech_locale
            )

        # 1. Quick Check for Conversational Greeting Patterns (Normalized)
        clean_prompt = re.sub(r"[?!.,।;:\'\"\-]", "", raw_text.lower()).strip()
        for phrase, (lang_code, natural_reply) in CONVERSATIONAL_GREETINGS.items():
            norm_phrase = re.sub(r"[?!.,।;:\'\"\-]", "", phrase.lower()).strip()
            if clean_prompt == norm_phrase or clean_prompt.startswith(norm_phrase + " ") or clean_prompt.endswith(" " + norm_phrase):
                profile = self.languages.get(lang_code, self.languages["en"])
                return DetectionResult(
                    language_code=profile.code,
                    language_name=profile.name,
                    native_name=profile.native_name,
                    script=profile.script,
                    confidence=0.98,
                    is_code_switched=False,
                    is_transliterated=False,
                    speech_locale=profile.speech_locale,
                    conversational_reply=natural_reply
                )

        # 2. Count Unicode Characters Per Indic Script
        script_counts = {
            "gu": len(re.findall(r"[\u0A80-\u0AFF]", raw_text)),
            "ta": len(re.findall(r"[\u0B80-\u0BFF]", raw_text)),
            "te": len(re.findall(r"[\u0C00-\u0C7F]", raw_text)),
            "kn": len(re.findall(r"[\u0C80-\u0CFF]", raw_text)),
            "ml": len(re.findall(r"[\u0D00-\u0D7F]", raw_text)),
            "bn": len(re.findall(r"[\u0980-\u09FF]", raw_text)),
            "pa": len(re.findall(r"[\u0A00-\u0A7F]", raw_text)),
            "devanagari": len(re.findall(r"[\u0900-\u097F]", raw_text)),
        }

        dominant_script = max(script_counts, key=script_counts.get)
        dominant_count = script_counts[dominant_script]

        # If significant native script is present (> 0 characters and dominant)
        if dominant_count > 0:
            if dominant_script == "devanagari":
                # Disambiguate Marathi vs Hindi in Devanagari
                mr_hits = sum(1 for m in MARATHI_SPECIFIC_MARKERS if m in raw_text)
                hi_hits = sum(1 for h in HINDI_SPECIFIC_MARKERS if h in raw_text)
                if mr_hits > hi_hits:
                    lang_code = "mr"
                elif hi_hits > mr_hits:
                    lang_code = "hi"
                else:
                    # Tie-breaker: typical Marathi indicators
                    if any(w in raw_text for w in ["आहे", "आहेत", "नाही", "नाहीत", "शिष्यवृत्ती", "वसतिगृह", "विद्यार्थ्यांसाठी", "च्या", "बद्दल"]):
                        lang_code = "mr"
                    else:
                        lang_code = "hi"

                profile = self.languages[lang_code]
                return DetectionResult(
                    language_code=profile.code,
                    language_name=profile.name,
                    native_name=profile.native_name,
                    script="Devanagari",
                    confidence=0.95,
                    is_code_switched=bool(re.search(r"\b[A-Za-z]{3,}\b", raw_text)),
                    is_transliterated=False,
                    speech_locale=profile.speech_locale
                )

            # Direct native Indic scripts (Gujarati, Tamil, Telugu, Bengali, Kannada, Malayalam, Punjabi)
            profile = self.languages.get(dominant_script, self.languages["en"])
            return DetectionResult(
                language_code=profile.code,
                language_name=profile.name,
                native_name=profile.native_name,
                script=profile.script,
                confidence=0.96,
                is_code_switched=bool(re.search(r"\b[A-Za-z]{3,}\b", raw_text)),
                is_transliterated=False,
                speech_locale=profile.speech_locale
            )

        # 3. Latin / Roman Script Analysis (Detecting English vs. Hinglish vs. Gujlish vs. Marathlish)
        words = [w.lower() for w in re.findall(r"\b[a-z]+\b", raw_text.lower())]
        if not words:
            profile = self.languages.get(fallback, self.languages["en"])
            return DetectionResult(
                language_code=profile.code,
                language_name=profile.name,
                native_name=profile.native_name,
                script="Latin",
                confidence=0.5,
                is_code_switched=False,
                is_transliterated=False,
                speech_locale=profile.speech_locale
            )

        words_set = set(words)
        gujlish_hits = len(words_set.intersection(GUJLISH_PATTERNS))
        hinglish_hits = len(words_set.intersection(HINGLISH_PATTERNS))
        marathlish_hits = len(words_set.intersection(MARATHLISH_PATTERNS))
        english_hits = len(words_set.intersection(COMMON_ENGLISH_WORDS))

        # Check for Gujlish greetings and grammar
        if gujlish_hits >= 1 and gujlish_hits >= hinglish_hits and gujlish_hits >= marathlish_hits:
            profile = self.languages["gu"]
            return DetectionResult(
                language_code="gu",
                language_name=profile.name,
                native_name=profile.native_name,
                script="Latin Transliterated (Gujlish)",
                confidence=0.88,
                is_code_switched=True,
                is_transliterated=True,
                speech_locale="gu-IN"
            )

        # Check for Marathlish
        if marathlish_hits >= 1 and marathlish_hits > hinglish_hits:
            profile = self.languages["mr"]
            return DetectionResult(
                language_code="mr",
                language_name=profile.name,
                native_name=profile.native_name,
                script="Latin Transliterated (Marathlish)",
                confidence=0.88,
                is_code_switched=True,
                is_transliterated=True,
                speech_locale="mr-IN"
            )

        # Check for Hinglish
        if hinglish_hits >= 1:
            profile = self.languages["hi"]
            return DetectionResult(
                language_code="hi",
                language_name=profile.name,
                native_name=profile.native_name,
                script="Latin Transliterated (Hinglish)",
                confidence=0.88,
                is_code_switched=True,
                is_transliterated=True,
                speech_locale="hi-IN"
            )

        # Default standard English
        profile = self.languages["en"]
        return DetectionResult(
            language_code="en",
            language_name=profile.name,
            native_name=profile.native_name,
            script="Latin",
            confidence=0.92,
            is_code_switched=False,
            is_transliterated=False,
            speech_locale="en-IN"
        )

    def get_language_info(self, language_code: str) -> Dict[str, Any]:
        """Return profile information as a dictionary for the given language code."""
        code = (language_code or "en").lower()
        if code in self.languages:
            p = self.languages[code]
            return {
                "code": p.code,
                "name": p.name,
                "native_name": p.native_name,
                "script": p.script,
                "speech_locale": p.speech_locale,
                "fallback_locale": p.fallback_locale,
                "tts_voice_names": p.tts_voice_names
            }
        p = self.languages["en"]
        return {
            "code": "en",
            "name": "English",
            "native_name": "English",
            "script": "Latin",
            "speech_locale": "en-IN",
            "fallback_locale": "en-US",
            "tts_voice_names": p.tts_voice_names
        }

    def get_speech_locale(self, language_code: str) -> str:
        """Return the standard BCP-47 speech recognition and synthesis locale code."""
        code = (language_code or "en").lower()
        if code in self.languages:
            return self.languages[code].speech_locale
        return "en-IN"

    def get_display_name(self, language_code: str) -> str:
        """Return the user-facing display name with native script label."""
        code = (language_code or "en").lower()
        if code in self.languages:
            p = self.languages[code]
            return f"{p.name} ({p.native_name})" if p.name != p.native_name else p.name
        return "English"


# Global singleton instance
language_service = CentralLanguageService()
