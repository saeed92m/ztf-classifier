(() => {
  "use strict";
  const API = "https://api.github.com/repos/saeed92m/ztf-classifier/releases?per_page=50";
  const KEY = "ztf-desktop-update-channel";
  let observer;
  const channel = () => {
    try { return localStorage.getItem(KEY) === "stable" ? "stable" : "preview"; }
    catch { return "preview"; }
  };
  const status = (node, message, kind) => {
    node.textContent = message;
    node.dataset.kind = kind || "info";
  };
  async function findRelease(selected) {
    const response = await fetch(API, { headers: { Accept: "application/vnd.github+json" }, cache: "no-store" });
    if (!response.ok) throw new Error("GitHub Releases returned HTTP " + response.status + ".");
    const releases = await response.json();
    const release = releases.find(item => !item.draft &&
      (selected === "preview" ? item.prerelease : !item.prerelease) &&
      (item.assets || []).some(asset => /-Setup\.exe$/i.test(asset.name)));
    if (!release) return null;
    const asset = release.assets.find(item => /-Setup\.exe$/i.test(item.name));
    if (!asset.digest || !/^sha256:[a-f0-9]{64}$/i.test(asset.digest)) {
      throw new Error("GitHub did not publish a valid SHA-256 digest for this installer.");
    }
    const url = new URL(asset.browser_download_url);
    if (url.hostname !== "github.com" || !url.pathname.startsWith("/saeed92m/ztf-classifier/releases/download/")) {
      throw new Error("Installer URL is outside the official project release path.");
    }
    return { release, asset };
  }
  async function download(asset, statusNode, button) {
    button.disabled = true;
    try {
      status(statusNode, "Downloading installer…", "info");
      const response = await fetch(asset.browser_download_url, { cache: "no-store" });
      if (!response.ok || !response.body) throw new Error("Installer download failed: HTTP " + response.status);
      const reader = response.body.getReader();
      const chunks = [];
      let received = 0;
      const total = Number(response.headers.get("Content-Length")) || asset.size || 0;
      while (true) {
        const part = await reader.read();
        if (part.done) break;
        chunks.push(part.value);
        received += part.value.byteLength;
        status(statusNode, total ? "Downloading installer… " + Math.min(100, Math.round(received * 100 / total)) + "%" : "Downloaded " + (received / 1048576).toFixed(1) + " MB…", "info");
      }
      if (asset.size && received !== asset.size) throw new Error("Downloaded file size does not match GitHub metadata.");
      const file = new Blob(chunks, { type: "application/vnd.microsoft.portable-executable" });
      const digest = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
      const actual = Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, "0")).join("");
      if (actual !== asset.digest.slice(7).toLowerCase()) throw new Error("SHA-256 verification failed. Download rejected.");
      const objectUrl = URL.createObjectURL(file);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = asset.name;
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(objectUrl), 60000);
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
      '<p class="muted">Download the latest Windows installer from the official GitHub Releases.</p>' +
      '<label class="desktop-update-label" for="desktopUpdateChannel">Update channel</label>' +
      '<select id="desktopUpdateChannel" class="desktop-update-select"><option value="stable">Stable — recommended</option><option value="preview">Preview — early access</option></select>' +
      '<div class="desktop-update-meta"><div><span>Latest version</span><strong id="desktopLatestVersion">Not checked</strong></div><div><span>Published</span><strong id="desktopLatestDate">—</strong></div></div>' +
      '<div id="desktopReleaseNotes" class="desktop-release-notes">Release notes appear after checking.</div>' +
      '<div class="desktop-update-actions"><button id="desktopCheckUpdates" class="secondary-button" type="button">Check for updates</button><button id="desktopDownloadUpdate" class="primary-button" type="button" hidden disabled>Download installer</button></div>' +
      '<p id="desktopUpdateStatus" class="muted" role="status" aria-live="polite">Select a channel and check GitHub Releases.</p>' +
      '<p class="muted">The installer is verified against GitHub’s SHA-256 digest. It is not executed automatically.</p>';
    const connectionPanel = Array.from(canvas.querySelectorAll(".panel")).find(node => node.textContent.includes("Connection status"));
    if (connectionPanel) canvas.insertBefore(panel, connectionPanel);
    else canvas.appendChild(panel);
    const select = panel.querySelector("#desktopUpdateChannel");
    const check = panel.querySelector("#desktopCheckUpdates");
    const downloadButton = panel.querySelector("#desktopDownloadUpdate");
    const message = panel.querySelector("#desktopUpdateStatus");
    select.value = channel();
    select.addEventListener("change", () => {
      try { localStorage.setItem(KEY, select.value); } catch { /* session-only preference */ }
      panel.querySelector("#desktopLatestVersion").textContent = "Not checked";
      panel.querySelector("#desktopLatestDate").textContent = "—";
      panel.querySelector("#desktopReleaseNotes").textContent = "Release notes appear after checking.";
      downloadButton.hidden = true;
      status(message, "Channel changed. Check again.", "info");
    });
    check.addEventListener("click", async () => {
      check.disabled = true;
      downloadButton.hidden = true;
      status(message, "Checking official GitHub Releases…", "info");
      try {
        const found = await findRelease(select.value);
        if (!found) {
          status(message, select.value === "stable" ? "No Stable Windows installer is published yet." : "No Preview Windows installer is available.", "warning");
          return;
        }
        panel.querySelector("#desktopLatestVersion").textContent = found.release.tag_name;
        panel.querySelector("#desktopLatestDate").textContent = found.release.published_at ? new Date(found.release.published_at).toLocaleString() : "Date unavailable";
        panel.querySelector("#desktopReleaseNotes").textContent = (found.release.body || "No release notes provided.").slice(0, 3000);
        downloadButton.hidden = false;
        downloadButton.disabled = false;
        downloadButton.onclick = () => download(found.asset, message, downloadButton);
        status(message, "Latest " + select.value.toUpperCase() + " Windows installer found. Installed-version comparison is not available in this build.", "success");
      } catch (error) {
        status(message, error.message || "Could not check GitHub Releases.", "error");
      } finally { check.disabled = false; }
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