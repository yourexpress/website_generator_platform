from __future__ import annotations

import io
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    app = create_app()
    app.dependency_overrides = {}
    return TestClient(app)


def login(client: TestClient) -> None:
    response = client.post("/auth/login", json={"username": "admin", "password": "change-me"})
    assert response.status_code == 200


def test_auth_required() -> None:
    client = make_client(Path("."))
    response = client.get("/api/projects")
    assert response.status_code == 401


def test_project_pipeline_with_export() -> None:
    client = make_client(Path("."))
    login(client)

    project = client.post("/api/projects", json={"name": "Northwind Studio", "summary": "Creative agency site"})
    assert project.status_code == 200
    project_id = project.json()["id"]

    upload = client.post(
        f"/api/projects/{project_id}/uploads",
        files={"files": ("hero.png", io.BytesIO(b"fake-image"), "image/png")},
    )
    assert upload.status_code == 200
    asset_id = upload.json()[0]["id"]

    requirement = client.post(
        f"/api/projects/{project_id}/requirements/refine",
        json={
            "selection": {"provider": "openai"},
            "input": {
                "prompt": "Build a polished brochure website for a creative design studio.",
                "business_name": "Northwind Studio",
                "business_type": "creative agency",
                "site_type": "brochure",
                "target_audience": ["startup founders", "marketing teams"],
                "brand_direction": "editorial, bright, premium",
                "required_sections": ["hero", "services", "case studies", "contact"],
                "cta_goals": ["Book a discovery call"],
                "reference_notes": "Use a bold hero and strong proof blocks.",
                "preferred_page_count": 2,
                "uploaded_asset_ids": [asset_id],
            },
        },
    )
    assert requirement.status_code == 200
    req_id = requirement.json()["id"]

    approved_req = client.post(f"/api/projects/{project_id}/requirements/approve", params={"requirement_version_id": req_id})
    assert approved_req.status_code == 200

    design = client.post(
        f"/api/projects/{project_id}/design/generate",
        json={"selection": {"provider": "claude"}, "requirement_version_id": req_id},
    )
    assert design.status_code == 200
    design_id = design.json()["id"]

    approved_design = client.post(f"/api/projects/{project_id}/design/approve", params={"design_version_id": design_id})
    assert approved_design.status_code == 200

    build = client.post(
        f"/api/projects/{project_id}/build/generate",
        json={"selection": {"provider": "deepseek"}, "design_version_id": design_id},
    )
    assert build.status_code == 200
    build_id = build.json()["id"]

    download = client.get(f"/api/projects/{project_id}/builds/{build_id}/download")
    assert download.status_code == 200
    archive = zipfile.ZipFile(io.BytesIO(download.content))
    assert "index.html" in archive.namelist()
    assert "styles.css" in archive.namelist()
    assert "manifest.json" in archive.namelist()


def test_provider_catalog() -> None:
    client = make_client(Path("."))
    login(client)
    response = client.get("/api/providers")
    assert response.status_code == 200
    names = {item["name"] for item in response.json()["providers"]}
    assert {"openai", "gemini", "claude", "deepseek"} <= names


def test_assistant_chat_auto_generates_preview() -> None:
    client = make_client(Path("."))
    login(client)

    project = client.post("/api/projects", json={"name": "Bluehaven Labs", "summary": "AI consulting website"})
    assert project.status_code == 200
    project_id = project.json()["id"]

    response = client.post(
        f"/api/projects/{project_id}/assistant/chat",
        json={
            "selection": {"provider": "gemini"},
            "message": "Create a polished brochure website for an AI consultancy focused on healthcare and operations leaders.",
            "site_type": "brochure",
            "preferred_page_count": 2,
            "uploaded_asset_ids": [],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["user_message"]["role"] == "user"
    assert body["assistant_message"]["role"] == "assistant"
    assert body["requirement_version"]["brief"]["project_name"] == "Bluehaven Labs"
    assert len(body["design_version"]["design"]["pages"]) >= 1

    project_detail = client.get(f"/api/projects/{project_id}")
    assert project_detail.status_code == 200
    detail = project_detail.json()
    assert len(detail["assistant_messages"]) == 2
    assert len(detail["requirement_versions"]) == 1
    assert len(detail["design_versions"]) == 1
