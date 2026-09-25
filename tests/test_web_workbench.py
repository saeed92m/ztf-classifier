from fastapi.testclient import TestClient

from ztf_classifier.api.app import create_app


def test_workbench_static_entrypoint_is_served() -> None:
    client = TestClient(create_app())
    response = client.get("/workbench/")
    assert response.status_code == 200
    assert "Scientific Analysis Workbench" in response.text


def test_workbench_theme_contract_is_present() -> None:
    client = TestClient(create_app())
    response = client.get("/workbench/styles.css")
    assert response.status_code == 200
    assert "--color-primary" in response.text
    assert '[data-theme="deep-space"]' in response.text
    assert '[data-theme="alpha"]' in response.text
    assert '[data-theme="light"]' in response.text
    assert '[data-theme="system"]' in response.text


def test_workbench_appearance_modes_are_present() -> None:
    client = TestClient(create_app())
    response = client.get("/workbench/")
    assert response.status_code == 200
    assert 'value="auto"' in response.text
    assert 'value="system"' in response.text
    assert 'value="deep-space"' in response.text
    assert 'value="alpha"' in response.text
    assert 'value="light"' in response.text


def test_workbench_light_curve_uses_observation_api() -> None:
    client = TestClient(create_app())
    response = client.get("/workbench/app.js")
    assert response.status_code == 200
    assert "/v1/objects/" in response.text
    assert "/observations?survey=" in response.text


def test_workbench_uses_durable_result_api_without_fabricated_values() -> None:
    client = TestClient(create_app())
    response = client.get("/workbench/app.js")
    assert response.status_code == 200
    assert "/results/latest?survey=" in response.text
    assert "Run analysis" in response.text

    page = client.get("/workbench/")
    assert "38.7%" not in page.text
    assert "267.1124" not in page.text
    assert "32.4198" not in page.text
    assert "α = 0.10" not in page.text
    assert "baseline_v0.2" not in page.text
    assert "267.1124" not in response.text


def test_workbench_workspace_views_use_real_catalog_job_and_report_contracts() -> None:
    client = TestClient(create_app())
    response = client.get("/workbench/app.js")

    assert response.status_code == 200
    assert "/v1/catalog/results?limit=100" in response.text
    assert "/v1/jobs?limit=100" in response.text
    assert "/v1/results/" in response.text
    assert "/report" in response.text
    assert "Reports not yet enabled" not in response.text
