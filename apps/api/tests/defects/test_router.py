import pytest
from httpx import AsyncClient
from uuid import uuid4

@pytest.mark.asyncio
async def test_defect_lifecycle_api(client: AsyncClient, admin_token_headers):
    # 1. Create Defect
    payload = {
        "title": "API Bug",
        "environment": "prod",
        "severity": "S2",
        "impact_area": "backend",
        "detected_by": "qa"
    }
    response = await client.post("/api/v1/defects/", json=payload, headers=admin_token_headers)
    assert response.status_code == 201
    defect = response.json()
    defect_id = defect["id"]
    assert defect["title"] == "API Bug"
    
    # 2. List Defects
    response = await client.get("/api/v1/defects/", headers=admin_token_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1
    
    # 3. Patch Defect (Triage)
    patch_payload = {"status": "triaged"}
    response = await client.patch(f"/api/v1/defects/{defect_id}", json=patch_payload, headers=admin_token_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "triaged"
    
    # 4. Get Timeline
    response = await client.get(f"/api/v1/defects/{defect_id}/timeline", headers=admin_token_headers)
    assert response.status_code == 200
    timeline = response.json()
    assert len(timeline) >= 2 # created + updated
    assert timeline[0]["event_type"] == "defect_created"
