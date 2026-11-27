from fastapi.testclient import TestClient

from ztf_classifier.api.app import create_app


def test_workbench_static_entrypoint_is_served() -> None:
    client = TestClient(create_app())
    response = client.get("/workbench/")
    assert response.status_code == 200
    assert "Scientific Analysis Workbench" in response.text
    assert 'src="./ztf-logo.svg"' in response.text
    logo = client.get("/workbench/ztf-logo.svg")
    assert logo.status_code == 200
    assert "<svg" in logo.text


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


def test_workbench_exposes_scientific_validation_dashboard() -> None:
    client = TestClient(create_app())
    page = client.get("/workbench/")
    script = client.get("/workbench/app.js")
    assert page.status_code == 200
    assert "Scientific Validation" in page.text
    assert script.status_code == 200
    assert "/v1/scientific-validation" in script.text


def test_desktop_mission_control_opens_the_selected_saved_result() -> None:
    client = TestClient(create_app())
    response = client.get("/workbench/app.js")

    assert response.status_code == 200
    assert 'await showView("overview", { result: record })' in response.text
    assert "async function showView(view, options = {})" in response.text
    assert "const selectedResult = options.result;" in response.text
    assert "state.survey = selectedResult.survey || state.survey;" in response.text
    assert "renderResult(selectedResult);" in response.text


def test_desktop_mission_control_dashboard_uses_live_api_evidence() -> None:
    client = TestClient(create_app())
    page = client.get("/workbench/")
    script = client.get("/workbench/app.js")
    styles = client.get("/workbench/styles.css")
    banner = client.get("/workbench/mission-control-banner.svg")

    assert page.status_code == 200
    assert script.status_code == 200
    assert styles.status_code == 200
    assert banner.status_code == 200
    assert "<svg" in banner.text
    assert 'url("./mission-control-banner.svg")' in styles.text
    assert "Scientific Mission Control" in script.text
    assert "mission-banner" in script.text
    assert "mission-main-grid" in styles.text
    assert ".canvas-header h1" in styles.text
    assert ".panel," in styles.text
    assert "input:focus" in styles.text
    assert 'fetchJson("/health")' in script.text
    assert 'fetchJson("/v1/workspaces")' in script.text
    assert 'fetchJson("/v1/workspaces/active")' in script.text
    assert 'fetchJson("/v1/model")' in script.text
    assert 'fetchJson("/v1/scientific-validation")' in script.text
    assert 'fetchJson("/v1/jobs?limit=5")' in script.text
    assert 'fetchJson("/v1/catalog/results?limit=8")' in script.text
    assert "no demo data" in script.text.lower()
    assert "ZTF20aaaaaaaa" not in script.text
    assert "0.0%" not in script.text


def test_desktop_updater_uses_authenticated_local_api_and_defaults_to_stable() -> None:
    client = TestClient(create_app())
    page = client.get("/workbench/")
    script = client.get("/workbench/desktop-updater.js")

    assert page.status_code == 200
    assert 'src="./desktop-updater.js"' in page.text
    assert "connect-src 'self'" in page.text
    assert script.status_code == 200
    assert "/v1/desktop/releases?channel=" in script.text
    assert "/v1/desktop/releases/" in script.text
    assert 'localStorage.getItem(KEY) === "preview" ? "preview" : "stable"' in script.text
    assert "api.github.com" not in script.text
    assert 'crypto.subtle.digest("SHA-256"' in script.text


def test_desktop_theme_and_sidebar_contracts_cover_light_mode() -> None:
    client = TestClient(create_app())
    styles = client.get("/workbench/styles.css")
    script = client.get("/workbench/app.js")

    assert styles.status_code == 200
    assert '[data-theme="light"] .sidebar' in styles.text
    assert '[data-theme="light"] .mission-panel' in styles.text
    assert '[data-theme="light"] .catalog-table-wrap' in styles.text
    assert "overflow-y: auto" in styles.text
    assert "height: calc(100vh - 78px)" in styles.text
    assert script.status_code == 200
    assert 'window.matchMedia("(prefers-color-scheme: light)")' in script.text


def test_desktop_updater_compares_installed_version_without_claiming_unknown_as_current() -> None:
    client = TestClient(create_app())
    script = client.get("/workbench/desktop-updater.js")

    assert script.status_code == 200
    assert "get_installed_version" in script.text
    assert "compareVersions(release.tag_name, installed)" in script.text
    assert "Update available:" in script.text
    assert "Up to date." in script.text
    assert "Installed version is unavailable" in script.text
    assert "Installed-version comparison is not available" not in script.text


def test_desktop_release_api_filters_stable_and_preview_installers(monkeypatch) -> None:
    import json

    import ztf_classifier.api.app as api_module

    digest = "sha256:" + ("a" * 64)
    def release(tag: str, prerelease: bool, name: str = "ZTF-Classifier-Setup.exe"):
        return {
            "tag_name": tag,
            "draft": False,
            "prerelease": prerelease,
            "published_at": "2026-11-27T08:00:00Z",
            "body": "Release notes",
            "assets": [{
                "name": name,
                "size": 1024,
                "digest": digest,
                "browser_download_url": (
                    "https://github.com/saeed92m/ztf-classifier/releases/download/"
                    + tag + "/" + name
                ),
            }],
        }

    payload = [
        release("v4.0.0-preview.1", True),
        release("v3.0.0", False),
        release("v2.0.0", False, "ztf_classifier.whl"),
        {**release("v1.0.0", False), "assets": [{
            "name": "ZTF-Classifier-Setup.exe",
            "size": 1024,
            "browser_download_url": "https://github.com/saeed92m/ztf-classifier/releases/download/v1.0.0/setup.exe",
        }]},
    ]

    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return None
        def read(self):
            return json.dumps(payload).encode("utf-8")

    monkeypatch.setattr(api_module, "urlopen", lambda *_args, **_kwargs: FakeResponse())
    client = TestClient(create_app())

    stable = client.get("/v1/desktop/releases?channel=stable")
    preview = client.get("/v1/desktop/releases?channel=preview")

    assert stable.status_code == 200
    assert stable.json()["release"]["tag_name"] == "v3.0.0"
    assert preview.status_code == 200
    assert preview.json()["release"]["tag_name"] == "v4.0.0-preview.1"


def test_desktop_release_api_rejects_unknown_channel() -> None:
    client = TestClient(create_app())
    response = client.get("/v1/desktop/releases?channel=nightly")
    assert response.status_code == 422



def _exercise_desktop_installer_download(
    monkeypatch,
    tmp_path,
    *,
    body: bytes,
    published_digest: str,
    published_size: int,
    final_url: str = (
        "https://release-assets.githubusercontent.com/github-production-release-asset/"
        "asset"
    ),
):
    import json

    import ztf_classifier.api.app as api_module

    asset_url = (
        "https://github.com/saeed92m/ztf-classifier/releases/download/"
        "v3.0.0/ZTF-Classifier-Setup.exe"
    )
    release_payload = [{
        "tag_name": "v3.0.0",
        "draft": False,
        "prerelease": False,
        "published_at": "2026-11-27T08:00:00Z",
        "body": "Release notes",
        "assets": [{
            "name": "ZTF-Classifier-Setup.exe",
            "size": published_size,
            "digest": published_digest,
            "browser_download_url": asset_url,
        }],
    }]

    class FakeResponse:
        def __init__(self, data: bytes, url: str | None = None):
            self.data = data
            self.url = url

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self, size: int = -1):
            if size < 0:
                chunk, self.data = self.data, b""
            else:
                chunk, self.data = self.data[:size], self.data[size:]
            return chunk

        def geturl(self):
            return self.url

    real_named_temporary_file = api_module.tempfile.NamedTemporaryFile

    def named_temporary_file(*args, **kwargs):
        kwargs["dir"] = tmp_path
        return real_named_temporary_file(*args, **kwargs)

    def fake_urlopen(request, timeout=0):
        request_url = request.full_url
        if request_url.startswith("https://api.github.com/"):
            return FakeResponse(json.dumps(release_payload).encode("utf-8"))
        if request_url == asset_url:
            return FakeResponse(body, final_url)
        raise AssertionError(f"Unexpected URL requested: {request_url}")

    monkeypatch.setattr(api_module, "urlopen", fake_urlopen)
    monkeypatch.setattr(
        api_module.tempfile,
        "NamedTemporaryFile",
        named_temporary_file,
    )
    response = TestClient(create_app()).get(
        "/v1/desktop/releases/v3.0.0/installer"
    )
    return response, tmp_path


def test_desktop_installer_proxy_returns_verified_executable_and_cleans_temp_file(
    monkeypatch, tmp_path
) -> None:
    import hashlib

    installer = b"MZ" + b"verified-installer-payload"
    response, temp_dir = _exercise_desktop_installer_download(
        monkeypatch,
        tmp_path,
        body=installer,
        published_digest="sha256:" + hashlib.sha256(installer).hexdigest(),
        published_size=len(installer),
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == (
        "application/vnd.microsoft.portable-executable"
    )
    assert response.content == installer
    assert list(temp_dir.iterdir()) == []


def test_desktop_installer_proxy_rejects_digest_mismatch_and_cleans_temp_file(
    monkeypatch, tmp_path
) -> None:
    import hashlib

    installer = b"MZ" + b"tampered-installer"
    wrong_digest = "sha256:" + hashlib.sha256(b"different-bytes").hexdigest()
    response, temp_dir = _exercise_desktop_installer_download(
        monkeypatch,
        tmp_path,
        body=installer,
        published_digest=wrong_digest,
        published_size=len(installer),
    )

    assert response.status_code == 502
    assert response.json()["code"] == "desktop_installer_digest_mismatch"
    assert list(temp_dir.iterdir()) == []


def test_desktop_installer_proxy_rejects_oversized_body_and_cleans_temp_file(
    monkeypatch, tmp_path
) -> None:
    installer = b"MZ" + b"oversized"
    response, temp_dir = _exercise_desktop_installer_download(
        monkeypatch,
        tmp_path,
        body=installer,
        published_digest="sha256:" + ("a" * 64),
        published_size=len(installer) - 1,
    )

    assert response.status_code == 502
    assert response.json()["code"] == "desktop_installer_size_invalid"
    assert list(temp_dir.iterdir()) == []


def test_desktop_installer_proxy_rejects_untrusted_redirect_and_cleans_temp_file(
    monkeypatch, tmp_path
) -> None:
    installer = b"MZ" + b"installer"
    response, temp_dir = _exercise_desktop_installer_download(
        monkeypatch,
        tmp_path,
        body=installer,
        published_digest="sha256:" + ("a" * 64),
        published_size=len(installer),
        final_url="https://attacker.example/installer.exe",
    )

    assert response.status_code == 502
    assert response.json()["code"] == "desktop_installer_host_invalid"
    assert list(temp_dir.iterdir()) == []


def test_desktop_installer_proxy_rejects_truncated_body_and_cleans_temp_file(
    monkeypatch, tmp_path
) -> None:
    installer = b"MZ" + b"short"
    response, temp_dir = _exercise_desktop_installer_download(
        monkeypatch,
        tmp_path,
        body=installer,
        published_digest="sha256:" + ("a" * 64),
        published_size=len(installer) + 10,
    )

    assert response.status_code == 502
    assert response.json()["code"] == "desktop_installer_size_mismatch"
    assert list(temp_dir.iterdir()) == []



def test_desktop_installer_proxy_rejects_insecure_redirect_scheme_and_cleans_temp_file(
    monkeypatch, tmp_path
) -> None:
    installer = b"MZ" + b"installer"
    response, temp_dir = _exercise_desktop_installer_download(
        monkeypatch,
        tmp_path,
        body=installer,
        published_digest="sha256:" + ("a" * 64),
        published_size=len(installer),
        final_url="http://github.com/saeed92m/ztf-classifier/installer.exe",
    )

    assert response.status_code == 502
    assert response.json()["code"] == "desktop_installer_host_invalid"
    assert list(temp_dir.iterdir()) == []
