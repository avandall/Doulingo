"""
TTS Service using gTTS (Google Text-to-Speech)
Supports accent dialects via TLD (e.g., 'co.in' for Indian English, 'co.uk' for British English, 'com.au' for Aussie English).
"""

import io
from gtts import gTTS

def generate_tts_mp3(text: str, lang: str = "en", tld: str = "com") -> io.BytesIO:
    """
    Generate MP3 binary audio stream from text using gTTS with specified accent TLD.
    """
    mp3_fp = io.BytesIO()
    try:
        tts = gTTS(text=text, lang=lang, tld=tld, slow=False)
    except Exception:
        # Fallback to standard 'com' TLD if specific TLD fails
        tts = gTTS(text=text, lang=lang, tld="com", slow=False)
    
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    return mp3_fp
