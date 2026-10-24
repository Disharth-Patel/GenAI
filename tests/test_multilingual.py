import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.ai_service import detect_language


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_automatic_language_detection():
    """Verify accurate detection of Hindi, Marathi, English, Hinglish, and regional scripts."""
    # Hindi (Devanagari)
    assert detect_language("महाराष्ट्र में ओबीसी छात्रों के लिए छात्रवृत्ति कैसे मिलेगी?") == "hi"
    assert detect_language("छात्रवृत्ति के लिए कौन से दस्तावेज़ चाहिए?") == "hi"

    # Marathi (Devanagari)
    assert detect_language("ओबीसी विद्यार्थ्यांसाठी कोणती शिष्यवृत्ती योजना आहे?") == "mr"
    assert detect_language("या योजनेसाठी अर्ज कसा करावा आणि कागदपत्रे कोणती लागतील?") == "mr"

    # English
    assert detect_language("What are the eligibility criteria for Post Matric Scholarship?") == "en"
    assert detect_language("How many seats are reserved in government colleges for OBC?") == "en"

    # Hinglish (Hindi in Roman script)
    assert detect_language("MahaDBT par scholarship ke liye apply kaise kare?") == "hinglish"
    assert detect_language("is me kitna allowance milta hai batao") == "hinglish"
    assert detect_language("mujhe hostel chahiye aur eligibility kya hai?") == "hinglish"

    # Gujarati
    assert detect_language("ગુજરાતી વિદ્યાર્થીઓ માટે સ્કોલરશીપ શું છે?") == "gu"

    # Tamil
    assert detect_language("தமிழ் மாணவர்களுக்கான கல்வி உதவித்தொகை என்ன?") == "ta"

    # Telugu
    assert detect_language("తెలుగు విద్యార్థుల స్కాలర్‌షిప్ పథకం ఏమిటి?") == "te"

    # Bengali
    assert detect_language("ওবিসি শিক্ষার্থীদের জন্য বৃত্তি কি?") == "bn"

    # Kannada
    assert detect_language("ಹಿಂದುಳಿದ ವರ್ಗಗಳ ವಿದ್ಯಾರ್ಥಿಗಳಿಗೆ ವಿದ್ಯಾರ್ಥಿವೇತನ ಯೋಜನೆಗಳು ಯಾವುವು?") == "kn"

    # Malayalam
    assert detect_language("ഒബിസി വിദ്യാർത്ഥികൾക്കുള്ള സ്കോളർഷിപ്പ് പദ്ധതികൾ ഏതെല്ലാമാണ്?") == "ml"

    # Punjabi
    assert detect_language("ਪੱਛੜੀਆਂ ਸ਼੍ਰੇਣੀਆਂ ਦੇ ਵਿਦਿਆਰਥੀਆਂ ਲਈ ਵਜ਼ੀਫ਼ਾ ਯੋਜਨਾ ਕੀ ਹੈ?") == "pa"

    # Gujlish (Gujarati code-switching)
    assert detect_language("OBC scholarship mate apply kem karvanu chhe?") == "gujlish"


def test_language_matched_responses(client):
    """Verify that chatbot automatically responds in the user's language by default."""
    # 1. Hindi query -> Hindi response
    hi_resp = client.post("/api/chat", json={
        "message": "महाराष्ट्र में ओबीसी छात्रों के लिए छात्रवृत्ति की जानकारी दीजिए।",
        "language": "auto"
    })
    assert hi_resp.status_code == 200
    hi_data = hi_resp.json()
    assert hi_data["language"] == "hi"
    assert any(term in hi_data["answer"] for term in ["छात्रवृत्ति", "पोर्टल", "ओबीसी", "महाडीबीटी", "योजना"])

    # 2. Marathi query -> Marathi response
    mr_resp = client.post("/api/chat", json={
        "message": "इतर मागासवर्गीय विद्यार्थ्यांसाठी पोस्ट मॅट्रिक शिष्यवृत्तीची माहिती सांगा.",
        "language": "auto"
    })
    assert mr_resp.status_code == 200
    mr_data = mr_resp.json()
    assert mr_data["language"] == "mr"
    assert any(term in mr_data["answer"] for term in ["शिष्यवृत्ती", "पोर्टल", "महाराष्ट्र", "ओबीसी"])

    # 3. Hinglish query -> Hinglish response
    hinglish_resp = client.post("/api/chat", json={
        "message": "OBC scholarship ke liye apply kaise kare aur documents kya chahiye?",
        "language": "auto"
    })
    assert hinglish_resp.status_code == 200
    h_data = hinglish_resp.json()
    assert h_data["language"] == "hinglish"
    assert any(term in h_data["answer"].lower() for term in ["portal", "mahadbt", "scholarship", "apply", "income", "eligibility"])

    # 4. English query -> English response
    en_resp = client.post("/api/chat", json={
        "message": "What is the foreign scholarship scheme for OBC students in Maharashtra?",
        "language": "auto"
    })
    assert en_resp.status_code == 200
    en_data = en_resp.json()
    assert en_data["language"] == "en"
    assert "scholarship" in en_data["answer"].lower()

    # 5. Gujarati query -> Gujarati response
    gu_resp = client.post("/api/chat", json={
        "message": "ઓબીસી વિદ્યાર્થીઓ માટે મહાદીબીટી સ્કોલરશીપ યોજના ની વિગતો આપો.",
        "language": "auto"
    })
    assert gu_resp.status_code == 200
    gu_data = gu_resp.json()
    assert gu_data["language"] == "gu"
    assert len(gu_data["answer"]) > 0

    # 6. Kannada query -> Kannada response
    kn_resp = client.post("/api/chat", json={
        "message": "ಹಿಂದುಳಿದ ವರ್ಗಗಳ ವಿದ್ಯಾರ್ಥಿಗಳಿಗೆ ವಿದ್ಯಾರ್ಥಿವೇತನ ಯೋಜನೆಗಳ ಮಾಹಿತಿ ನೀಡಿ.",
        "language": "auto"
    })
    assert kn_resp.status_code == 200
    kn_data = kn_resp.json()
    assert kn_data["language"] == "kn"
    assert len(kn_data["answer"]) > 0


def test_context_awareness_across_language_switching(client):
    """
    Verify conversational context is maintained when user switches languages mid-conversation:
    Turn 1: User asks in English about Savitribai Phule hostel allowance.
    Turn 2: User switches to Hindi ('इसमें कितना भत्ता मिलता है?') with anaphoric reference.
    Turn 3: User switches to Hinglish ('aur apply kaise karein?') maintaining context.
    """
    # Turn 1: English
    t1 = client.post("/api/chat", json={
        "message": "Tell me about the Gyanjyoti Savitribai Phule Aadhaar hostel allowance scheme.",
        "language": "auto"
    })
    assert t1.status_code == 200
    conv_id = t1.json()["conversation_id"]
    assert "savitribai" in t1.json()["answer"].lower() or any("savitribai" in s["title"].lower() for s in t1.json()["sources"])

    # Turn 2: Follow up in Hindi ('इसमें कितना भत्ता मिलता है?')
    t2 = client.post("/api/chat", json={
        "message": "इसमें कितना भत्ता मिलता है?",
        "conversation_id": conv_id,
        "language": "auto"
    })
    assert t2.status_code == 200
    t2_data = t2.json()
    assert t2_data["conversation_id"] == conv_id
    assert t2_data["language"] in ["hi", "mr"]
    # Context retained: sources or answer should mention Savitribai Phule or allowance
    assert any("savitribai" in s["title"].lower() or "hostel" in s["title"].lower() or "भत्ता" in s["title"] for s in t2_data["sources"])

    # Turn 3: Follow up in Hinglish ('aur apply kaise karein?')
    t3 = client.post("/api/chat", json={
        "message": "aur iska application kaise bharein?",
        "conversation_id": conv_id,
        "language": "auto"
    })
    assert t3.status_code == 200
    t3_data = t3.json()
    assert t3_data["conversation_id"] == conv_id
    assert t3_data["language"] == "hinglish"
    assert len(t3_data["sources"]) > 0


def test_unsupported_or_ambiguous_language_fallback(client):
    """Verify fallback handling when language is unrecognizable/gibberish."""
    # When random symbols/gibberish sent
    res = client.post("/api/chat", json={
        "message": "%%% ^^^ &&& ???",
        "language": "auto"
    })
    assert res.status_code == 200
    data = res.json()
    # The assistant politely clarifies or offers supported languages
    ans = data["answer"].lower()
    assert (
        "support" in ans or "language" in ans or "clarif" in ans or "please" in ans or
        "भाषा" in data["answer"] or "स्पष्ट" in data["answer"] or "प्रश्न" in data["answer"] or "जानकारी" in data["answer"]
    )
