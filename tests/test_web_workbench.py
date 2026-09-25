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
