"""Chat & Turn Pydantic Models."""
from pydantic import BaseModel


class TurnRequest(BaseModel):
    scenario_id: str
    character_id: str | None = None
    user_transcript: str
    conversation_history: list[dict[str, str]] = []
    level: int | None = 1


class ChatRequest(BaseModel):
    user_transcript: str | None = None
    text: str | None = None
    scenario_id: str | None = "everyday_chat"
    character_id: str | None = None
    conversation_history: list[dict[str, str]] = []
    level: int | None = 1


class StartScenarioRequest(BaseModel):
    scenario_id: str
    character_id: str | None = None
    level: int | None = 1


class VoiceTurnRequest(BaseModel):
    user_id: str = "user_demo"
    topic: str = "general_conversation"
    band_level: float = 5.5
    level: int | None = None
    conversation_history: list[dict[str, str]] = []
    character_id: str | None = "lily"
    text_only_mode: bool = False
    user_transcript: str | None = None
    audio_base64: str | None = None


class SentenceTranslateRequest(BaseModel):
    text: str
    target_lang: str | None = "vi"
    character_name: str | None = ""
    scenario_title: str | None = ""
    context_history: list[str] | None = []


class DetSpeechEvalRequest(BaseModel):
    scenario_id: str
    user_speech: str
    duration_seconds: int | None = 120
    mode: str | None = "read_then_speak"
    wpm: int | None = None
    pause_count: int | None = None
    filler_count: int | None = None
