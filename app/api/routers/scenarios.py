"""Scenarios & Characters API Router."""
import logging
import uuid

from fastapi import APIRouter, HTTPException

from app.api.schemas.scenarios import CustomScenarioRequest, ScenarioImportRequest
from app.characters import get_character, list_characters
from app.scenarios import get_scenario, list_scenarios
from app.storage import add_custom_scenario, delete_custom_scenario, get_custom_scenarios

logger = logging.getLogger("duolingo_speak.api.scenarios")
router = APIRouter(tags=["Scenarios & Characters"])


@router.get("/api/scenarios")
def api_list_scenarios():
    return {"scenarios": list_scenarios()}


@router.get("/api/scenarios/{scenario_id}")
def api_get_scenario(scenario_id: str):
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.post("/api/custom_scenarios")
def api_create_custom_scenario(payload: CustomScenarioRequest):
    if not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    prefix = "det_custom_" if payload.mode == "ielts_exam" else "custom_"
    sc_id = f"{prefix}{uuid.uuid4().hex[:8]}"
    sc_data = {
        "id": sc_id,
        "title": payload.title,
        "category": payload.category,
        "icon": payload.icon or "💬",
        "color": payload.color or "#1CB0F6",
        "level": payload.level or "Beginner",
        "level_code": payload.level_code or "A2",
        "default_character": payload.default_character or "rajesh",
        "description": payload.description or "Everyday life topic",
        "objective": payload.objective or "Express thoughts freely.",
        "suggested_vocabulary": payload.suggested_vocabulary or ["Everyday chat"],
        "mode": payload.mode or "roleplay",
    }
    saved = add_custom_scenario(sc_data)
    return {"status": "success", "scenario": saved}


@router.delete("/api/custom_scenarios/{scenario_id}")
def api_delete_custom_scenario(scenario_id: str):
    deleted = delete_custom_scenario(scenario_id)
    return {"status": "success", "deleted": deleted, "id": scenario_id}


@router.get("/api/custom_scenarios/export/{scenario_id}")
def api_export_custom_scenario(scenario_id: str):
    logger.info(f"Exporting scenario: {scenario_id}")
    if scenario_id == "all":
        custom_scenarios = get_custom_scenarios()
        return {"scenarios": custom_scenarios, "count": len(custom_scenarios)}

    scenario = get_scenario(scenario_id)
    if not scenario:
        logger.error(f"Scenario not found for export: {scenario_id}")
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {"scenario": scenario}


@router.post("/api/custom_scenarios/import")
def api_import_custom_scenarios(payload: ScenarioImportRequest):
    if not payload.scenarios:
        raise HTTPException(status_code=400, detail="Scenarios list cannot be empty")

    logger.info(f"Importing {len(payload.scenarios)} custom scenario(s)")
    imported = []
    for item in payload.scenarios:
        if not item.title.strip():
            continue
        prefix = "det_custom_" if item.mode == "ielts_exam" else "custom_"
        sc_id = f"{prefix}{uuid.uuid4().hex[:8]}"
        sc_data = {
            "id": sc_id,
            "title": item.title.strip(),
            "category": item.category or "Custom Topic",
            "icon": item.icon or "💬",
            "color": item.color or "#1CB0F6",
            "level": item.level or "Beginner",
            "level_code": item.level_code or "A2",
            "default_character": item.default_character or "rajesh",
            "description": item.description or "Imported topic",
            "objective": item.objective or "Express thoughts freely.",
            "suggested_vocabulary": item.suggested_vocabulary or ["Imported chat"],
            "mode": item.mode or "roleplay",
        }
        saved = add_custom_scenario(sc_data)
        imported.append(saved)

    return {"status": "success", "imported_count": len(imported), "scenarios": imported}


@router.get("/api/characters")
def api_list_characters():
    return {"characters": list_characters()}


@router.get("/api/characters/{character_id}")
def api_get_character(character_id: str):
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character
