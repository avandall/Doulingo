"""
Unit tests for Custom Scenario Sharing & Export API endpoints
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_export_all_scenarios():
    response = client.get("/api/custom_scenarios/export/all")
    assert response.status_code == 200
    data = response.json()
    assert "scenarios" in data
    assert "count" in data
    assert isinstance(data["scenarios"], list)

def test_export_single_builtin_scenario():
    response = client.get("/api/custom_scenarios/export/det_childhood_memory")
    assert response.status_code == 200
    data = response.json()
    assert "scenario" in data
    assert data["scenario"]["id"] == "det_childhood_memory"
    assert data["scenario"]["title"] == "Childhood Memories"

def test_export_nonexistent_scenario():
    response = client.get("/api/custom_scenarios/export/nonexistent_scenario_12345")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Scenario not found"

def test_import_custom_scenarios():
    payload = {
        "scenarios": [
            {
                "title": "Shared Coffee Chat",
                "category": "Everyday Life ☕",
                "icon": "☕",
                "color": "#1CB0F6",
                "level": "Beginner",
                "level_code": "A2",
                "default_character": "rajesh",
                "description": "A shared custom scenario for practicing ordering coffee.",
                "objective": "Order coffee and pastries.",
                "suggested_vocabulary": ["Latte", "Croissant", "Espresso"],
                "mode": "roleplay"
            }
        ]
    }
    response = client.post("/api/custom_scenarios/import", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["imported_count"] == 1
    assert len(data["scenarios"]) == 1
    imported_sc = data["scenarios"][0]
    assert imported_sc["title"] == "Shared Coffee Chat"
    assert imported_sc["id"].startswith("custom_")

    # Verify that the exported scenario can be retrieved
    export_res = client.get(f"/api/custom_scenarios/export/{imported_sc['id']}")
    assert export_res.status_code == 200
    exported_data = export_res.json()
    assert exported_data["scenario"]["title"] == "Shared Coffee Chat"

    # Clean up test scenario from DB
    from app.storage.db import delete_custom_scenario
    delete_custom_scenario(imported_sc["id"])


def test_import_empty_list_returns_400():
    response = client.post("/api/custom_scenarios/import", json={"scenarios": []})
    assert response.status_code == 400
    assert response.json()["detail"] == "Scenarios list cannot be empty"
