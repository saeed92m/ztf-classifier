(() => {
  "use strict";
  const KEY = "ztf-desktop-update-channel";
  let observer;

  const channel = () => {
    try { return localStorage.getItem(KEY) === "preview" ? "preview" : "stable"; }
    catch { return "stable"; }
  };
  const status = (node, message, kind) => {
    node.textContent = message;
    node.dataset.kind = kind || "info";
  };
  async function apiFetch(url, options = {}) {
    const headers = { ...(options.headers || {}) };
    const token = await window.getDesktopApiToken();
    if (token) headers.Authorization = "Bearer " + token;
    return fetch(url, { ...options, headers, cache: "no-store" });
  }
  function parseVersion(value) {
    const match = String(value || "").trim().match(/^(?:desktop-v|v)?(\\d+)\\.(\\d+)\\.(\\d+)(?:-([0-9A-Za-z.-]+))?$/);
    if (!match) return null;
    return { major: Number(match[1]), minor: Number(match[2]), patch: Number(match[3]),
      prerelease: match[4] ? match[4].split(".") : null };
  }
  function compareVersions(left, right) {
    const a = parseVersion(left), b = parseVersion(right);
    if (!a || !b) return null;
    for (const key of ["major", "minor", "patch"]) {
      if (a[key] !== b[key]) return a[key] > b[key] ? 1 : -1;
    }
    if (a.prerelease === null && b.prerelease === null) return 0;
    if (a.prerelease === null) return 1;
    if (b.prerelease === null) return -1;
    const length = Math.max(a.prerelease.length, b.prerelease.length);
    for (let i = 0; i < length; i += 1) {
      if (a.prerelease[i] === undefined) return -1;
      if (b.prerelease[i] === undefined) return 1;
      if (a.prerelease[i] === b.prerelease[i]) continue;
      const an = /^\\d+$/.test(a.prerelease[i]), bn = /^\\d+$/.test(b.prerelease[i]);
      if (an && bn) return Number(a.prerelease[i]) > Number(b.prerelease[i]) ? 1 : -1;
      if (an !== bn) return an ? -1 : 1;
      return a.prerelease[i] > b.prerelease[i] ? 1 : -1;
    }
    return 0;
  }
  async function installedVersion() {
    const getter = window.pywebview?.api?.get_installed_version;
    if (typeof getter !== "function") return null;
    try { return await getter(); } catch { return null; }
  }
  async function findRelease(selected) {
    const response = await apiFetch("/v1/desktop/releases?channel=" + encodeURIComponent(selected), {
      headers: { Accept: "application/json" }
    });
    if (!response.ok) throw new Error("Update service returned HTTP " + response.status + ".");
    const payload = await response.json();
    return payload.release || null;
  }
  async function download(release, statusNode, button) {
    button.disabled = true;
    try {
      status(statusNode, "Downloading and verifying installer…", "info");
      const response = await apiFetch(
        "/v1/desktop/releases/" + encodeURIComponent(release.tag_name) + "/installer"
      );
      if (!response.ok) throw new Error("Installer download or server-side verification failed (HTTP " + response.status + ").");
      const file = await response.blob();
      if (file.size !== release.size) throw new Error("Downloaded file size does not match GitHub metadata.");
      const digest = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
      const actual = Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, "0")).join("");
      if (actual !== release.digest.slice(7).toLowerCase()) {
        throw new Error("SHA-256 verification failed. Download rejected.");
      }
      const objectUrl = URL.createObjectURL(file);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = release.name;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60000);
      status(statusNode, "Download complete. SHA-256 verified. Close the app, then run the installer manually.", "success");
    } catch (error) {
      status(statusNode, error.message || "Download failed.", "error");
    } finally {
      button.disabled = false;
    }
  }
  function attach() {
    const title = document.getElementById("viewTitle");
    const canvas = document.querySelector(".main-canvas");
    if (!title || !canvas || title.textContent.trim() !== "Settings" || canvas.querySelector("#desktopReleaseUpdater")) return;

    const panel = document.createElement("section");
    panel.id = "desktopReleaseUpdater";
    panel.className = "panel desktop-update-panel";
    panel.innerHTML = '<div class="panel-title">Software Update</div>' +
      '<p class="muted">Check and download a verified Windows installer from the official project release channel.</p>' +
      '<label class="desktop-update-label" for="desktopUpdateChannel">Update channel</label>' +
      '<select id="desktopUpdateChannel" class="desktop-update-select"><option value="stable">Stable — recommended</option><option value="preview">Preview — early access</option></select>' +
      '<div class="desktop-update-meta"><div><span>Installed version</span><strong id="desktopInstalledVersion">Checking…</strong></div><div><span>Latest available</span><strong id="desktopLatestVersion">Not checked</strong></div><div><span>Published</span><strong id="desktopLatestDate">—</strong></div></div>' +
      '<div id="desktopReleaseNotes" class="desktop-release-notes">Release notes appear after checking.</div>' +
      '<div class="desktop-update-actions"><button id="desktopCheckUpdates" class="secondary-button" type="button">Check for updates</button><button id="desktopDownloadUpdate" class="primary-button" type="button" hidden disabled>Download installer</button></div>' +
      '<p id="desktopUpdateStatus" class="muted" role="status" aria-live="polite">Select a channel and check for a published release.</p>' +
      '<p class="muted">The server and desktop client verify SHA-256. The installer is not executed automatically.</p>';
    const connectionPanel = Array.from(canvas.querySelectorAll(".panel"))
      .find(node => node.textContent.includes("Connection status"));
    if (connectionPanel) canvas.insertBefore(panel, connectionPanel);
    else canvas.appendChild(panel);

    const select = panel.querySelector("#desktopUpdateChannel");
    const check = panel.querySelector("#desktopCheckUpdates");
    const downloadButton = panel.querySelector("#desktopDownloadUpdate");
    const message = panel.querySelector("#desktopUpdateStatus");
    select.value = channel();

    select.addEventListener("change", () => {
      try { localStorage.setItem(KEY, select.value); } catch { /* session-only preference */ }
      panel.querySelector("#desktopInstalledVersion").textContent = "Checking…";
      panel.querySelector("#desktopLatestVersion").textContent = "Not checked";
      panel.querySelector("#desktopLatestDate").textContent = "—";
      panel.querySelector("#desktopReleaseNotes").textContent = "Release notes appear after checking.";
      downloadButton.hidden = true;
      status(message, "Channel changed. Check again.", "info");
    });

    check.addEventListener("click", async () => {
      check.disabled = true;
      downloadButton.hidden = true;
      status(message, "Checking the official release service…", "info");
      try {
        const installed = await installedVersion();
        const installedNode = panel.querySelector("#desktopInstalledVersion");
        installedNode.textContent = installed || "Unavailable";
        const release = await findRelease(select.value);
        if (!release) {
          status(message, select.value === "stable"
            ? "No Stable Windows installer is published yet."
            : "No Preview Windows installer is available.", "warning");
          return;
        }
        panel.querySelector("#desktopLatestVersion").textContent = release.tag_name;
        panel.querySelector("#desktopLatestDate").textContent = release.published_at
          ? new Date(release.published_at).toLocaleString()
          : "Date unavailable";
        panel.querySelector("#desktopReleaseNotes").textContent = release.body || "No release notes provided.";
        downloadButton.hidden = false;
        downloadButton.disabled = false;
        downloadButton.onclick = () => download(release, message, downloadButton);
        const comparison = installed ? compareVersions(release.tag_name, installed) : null;
        if (comparison === 1) {
          status(message, "Update available: " + installed + " → " + release.tag_name + ".", "success");
        } else if (comparison === 0) {
          status(message, "Up to date. Installed version matches the latest " + select.value.toUpperCase() + " release.", "success");
        } else if (comparison === -1) {
          status(message, "Installed version (" + installed + ") is newer than the latest " + select.value.toUpperCase() + " release (" + release.tag_name + ").", "warning");
        } else if (!installed) {
          status(message, "Latest release found. Installed version is unavailable, so comparison cannot be completed.", "warning");
        } else {
          status(message, "Latest release found, but version format is not supported. No comparison was made.", "warning");
        }
      } catch (error) {
        status(message, error.message || "Could not check for updates.", "error");
      } finally {
        check.disabled = false;
      }
    });
  }

  function start() {
    attach();
    observer = new MutationObserver(attach);
    observer.observe(document.body, { childList: true, subtree: true, characterData: true });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start, { once: true });
  else start();
})();