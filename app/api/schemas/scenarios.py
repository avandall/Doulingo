"""Scenario Request & Response Models."""
from pydantic import BaseModel


class CustomScenarioRequest(BaseModel):
    title: str
    category: str | None = "Everyday Life ☕"
    icon: str | None = "💬"
    color: str | None = "#1CB0F6"
    level: str | None = "Beginner"
    level_code: str | None = "A2"
    default_character: str | None = "rajesh"
    description: str | None = "Custom everyday life topic"
    objective: str | None = "Express your thoughts freely."
    suggested_vocabulary: list[str] | None = ["Everyday conversation", "Free chat"]
    mode: str | None = "roleplay"


class ScenarioImportRequest(BaseModel):
    scenarios: list[CustomScenarioRequest]
