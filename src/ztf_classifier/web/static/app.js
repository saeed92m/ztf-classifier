
const STORAGE_KEY = "ztf-workbench-appearance";
const defaults = { theme: "auto", dayStart: "06:00", nightStart: "18:00" };
const params = new URLSearchParams(window.location.search);
const desktopMode = params.get("desktop") === "1";
let desktopDr24Payload = null;
let desktopRawExport = null;
let desktopRawExportPersisted = false;
function desktopTranslate(value) { return value; }
function translateDesktopText() {}

const state = {
  oid: params.get("oid") || "",
  survey: params.get("survey") || "ztf",
  observations: [],
  result: null,
};
let storedSettings = { theme: "system", workspace_directory: null, max_import_bytes: 250 * 1024 * 1024, day_start: "06:00", night_start: "18:00" };
function localPreferences() {
  try { return { ...defaults, ...JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}") }; }
  catch { return { ...defaults }; }
}
function timeToMinutes(value) {
  const parts = value.split(":").map(Number);
  return parts[0] * 60 + parts[1];
}
function resolveTheme(p) {
  if (["deep-space", "alpha", "light"].includes(p.theme)) return p.theme;
  if (p.theme === "system") return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "system";
  const minutes = new Date().getHours() * 60 + new Date().getMinutes();
  const day = timeToMinutes(p.dayStart), night = timeToMinutes(p.nightStart);
  const isDay = day < night ? minutes >= day && minutes < night : minutes >= day || minutes < night;
  return isDay ? "light" : "alpha";
}
function applyTheme(p) { document.documentElement.dataset.theme = resolveTheme(p); }
function readPreferencesFromServer(payload) {
  storedSettings = { ...storedSettings, ...payload };
  return { theme: payload.theme || defaults.theme, dayStart: payload.day_start || defaults.dayStart, nightStart: payload.night_start || defaults.nightStart };
}
async function persistPreferences(p) {
  const body = { ...storedSettings, theme: p.theme, day_start: p.dayStart, night_start: p.nightStart };
  try {
    const saved = await fetchJson("/v1/settings", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    storedSettings = saved;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(p));
    setConnectionState("Settings saved", true);
  } catch {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(p));
    setConnectionState("Settings local only", false);
  }
  applyTheme(p);
}
async function initializePreferences() {
  let preferences;
  try {
    preferences = readPreferencesFromServer(await fetchJson("/v1/settings"));
    if (desktopMode) setConnectionState("API ready", true);
  } catch {
    preferences = localPreferences();
    if (desktopMode) setConnectionState("Local settings unavailable", false);
  }
  applyTheme(preferences);
  const themeButton = document.getElementById("themeButton");
  const popover = document.getElementById("themePopover");
  const themeSelect = document.getElementById("themeSelect");
  const dayStart = document.getElementById("dayStart");
  const nightStart = document.getElementById("nightStart");
  themeSelect.value = preferences.theme;
  dayStart.value = preferences.dayStart;
  nightStart.value = preferences.nightStart;
  themeButton.addEventListener("click", () => { popover.hidden = !popover.hidden; });
  themeSelect.addEventListener("change", () => { preferences.theme = themeSelect.value; void persistPreferences(preferences); });
  dayStart.addEventListener("change", () => { preferences.dayStart = dayStart.value; void persistPreferences(preferences); });
  nightStart.addEventListener("change", () => { preferences.nightStart = nightStart.value; void persistPreferences(preferences); });
  setInterval(() => { if (preferences.theme === "auto") applyTheme(preferences); }, 60000);
}
void initializePreferences();

function setConnectionState(label, ok) {
  const node = document.querySelector(".connection-state");
  if (!node) return;
  node.innerHTML = '<span class="status-dot"></span>' + desktopTranslate(label);
  node.querySelector(".status-dot").style.background =
    ok === false ? "var(--color-warning)" : "var(--color-success)";
}
function setObjectIdentity() {
  const label = state.oid || "Select an object";
  document.getElementById("viewTitle").textContent = label;
  document.querySelector(".object-identity strong").textContent = label;
}
function escapeHtml(value) {
  return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
}
let desktopTokenPromise = null;
function getDesktopApiToken() {
  if (params.get("desktop") !== "1") return Promise.resolve(null);
  if (!desktopTokenPromise) {
    const pending = new Promise((resolve, reject) => {
      let timeout = null;
      const readToken = () => {
        const getter = window.pywebview?.api?.get_api_token;
        if (typeof getter !== "function") return false;
        if (timeout !== null) window.clearTimeout(timeout);
        Promise.resolve().then(() => getter()).then(resolve, reject);
        return true;
      };
      if (readToken()) return;
      timeout = window.setTimeout(
        () => reject(new Error("Desktop authentication bridge did not become ready.")),
        10000
      );
      window.addEventListener("pywebviewready", () => {
        if (!readToken()) {
          reject(new Error("Desktop authentication bridge is unavailable."));
        }
      }, { once: true });
    });
    desktopTokenPromise = pending.catch(error => {
      desktopTokenPromise = null;
      throw error;
    });
  }
  return desktopTokenPromise;
}

if (params.get("desktop") === "1") {
  document.addEventListener("click", event => {
    const anchor = event.target instanceof Element
      ? event.target.closest("a[href]")
      : null;
    if (!anchor) return;
    const target = new URL(anchor.getAttribute("href"), window.location.href);
    if (target.origin !== window.location.origin) {
      event.preventDefault();
      event.stopImmediatePropagation();
    }
  }, true);
  window.open = () => null;
}

async function fetchJson(url, options) {
  const headers = {
    Accept: "application/json",
    ...((options && options.headers) || {}),
  };
  const token = await getDesktopApiToken();
  if (token) headers.Authorization = "Bearer " + token;
  const response = await fetch(url, {
    ...(options || {}),
    headers,
  });
  if (!response.ok) { const error = new Error("HTTP " + response.status); error.status = response.status; throw error; }
  return response.json();
}
function clearPrediction() {
  document.getElementById("predictedClass").textContent = "—";
  document.getElementById("topProbability").textContent = "—";
  document.getElementById("conformalSet").textContent = "—";
  document.getElementById("conformalAlpha").textContent = "conformal coverage";
  document.getElementById("oodPercentile").textContent = "—";
  document.getElementById("probabilityList").innerHTML =
    '<div class="muted">No durable scientific result loaded.</div>';
  document.getElementById("featureSchema").textContent = "—";
  document.getElementById("modelValue").textContent = "—";
  document.getElementById("calibrationValue").textContent = "—";
  document.getElementById("oodValue").textContent = "—";
  document.getElementById("provenanceValue").textContent = "—";
  document.getElementById("calibrationState").textContent = "—";
  document.getElementById("conformalState").textContent = "—";
  document.getElementById("oodState").textContent = "—";
  document.getElementById("datasetProvenance").textContent = "—";
  document.getElementById("modelProvenance").textContent = "—";
  document.getElementById("schemaProvenance").textContent = "—";
}

function renderPrediction(prediction) {
  if (!prediction) {
    clearPrediction();
    return;
  }
  const probabilities = Object.entries(prediction.probabilities || {}).sort((a, b) => b[1] - a[1]);
  const top = probabilities[0];
  document.getElementById("predictedClass").textContent = prediction.predicted_class || "—";
  document.getElementById("topProbability").textContent = top ? (top[1] * 100).toFixed(1) + "%" : "—";
  const rows = document.getElementById("probabilityList");
  rows.innerHTML = "";
  probabilities.slice(0, 8).forEach(([label, probability]) => {
    const row = document.createElement("div");
    row.className = "prob-row";
    row.innerHTML = "<span>" + escapeHtml(label) + "</span><div class=\"bar\"><i style=\"width:" +
      Math.max(0, Math.min(100, probability * 100)).toFixed(2) + "%\"></i></div><b>" +
      (probability * 100).toFixed(1) + "%</b>";
    rows.appendChild(row);
  });
  const conformal = prediction.conformal || [];
  document.getElementById("conformalSet").textContent =
    conformal.length ? conformal[0].prediction_set_size + " classes" : "—";
  document.getElementById("conformalAlpha").textContent =
    conformal.length && conformal[0].alpha != null
      ? "α = " + Number(conformal[0].alpha).toFixed(2)
      : "conformal coverage";
  const ood = prediction.ood;
  document.getElementById("oodPercentile").textContent =
    ood && ood.anomaly_percentile != null ? Number(ood.anomaly_percentile).toFixed(1) : "—";
}
function renderResult(record, durable = true) {
  state.result = record;
  const payload = record.payload || {};
  renderPrediction(payload.prediction);
  document.getElementById("viewSubtitle").textContent =
    (durable ? "Durable scientific result · " : "Live analysis result · ") + record.schema_version + " · " + record.model_version;
  document.getElementById("featureSchema").textContent = payload.feature_schema_version || "—";
  document.getElementById("objectIdValue").textContent = record.oid || state.oid || "—";
  document.getElementById("modelChip").textContent = record.model_version || "—";
  document.getElementById("modelValue").textContent =
    record.model_version + " · " + (payload.model_family || "—");
  document.getElementById("calibrationValue").textContent =
    (payload.diagnostics || {}).calibration || "—";
  document.getElementById("oodValue").textContent = (payload.diagnostics || {}).ood || "—";
  document.getElementById("provenanceValue").textContent =
    payload.observation_provenance ? "source-backed" : "stored result";
  document.getElementById("calibrationState").textContent =
    (payload.diagnostics || {}).calibration || "—";
  document.getElementById("conformalState").textContent =
    (payload.diagnostics || {}).conformal || "—";
  document.getElementById("oodState").textContent =
    (payload.diagnostics || {}).ood || "—";
  document.getElementById("datasetProvenance").textContent =
    payload.observation_provenance?.source || "—";
  document.getElementById("modelProvenance").textContent =
    payload.model_provenance?.model_version || record.model_version || "—";
  document.getElementById("schemaProvenance").textContent =
    payload.feature_schema_version || record.schema_version || "—";
  document.getElementById("resultState").textContent = "complete";
  renderLightCurve(document.getElementById("lightCurveSvg"), payload.observations || state.observations);
}
function renderLightCurve(svg, observations) {
  if (!svg) return;
  svg.querySelectorAll(".dynamic-light-curve, .chart-message").forEach(node => node.remove());
  const usable = observations.map(item => ({ mjd: Number(item.mjd), mag: Number(item.mag) }))
    .filter(item => Number.isFinite(item.mjd) && Number.isFinite(item.mag));
  if (!usable.length) {
    svg.insertAdjacentHTML("beforeend",
      '<text x="450" y="140" text-anchor="middle" class="chart-message">No photometric points available</text>');
    return;
  }
  const xs = usable.map(item => item.mjd), ys = usable.map(item => item.mag);
  const xmin = Math.min(...xs), xmax = Math.max(...xs), ymin = Math.min(...ys), ymax = Math.max(...ys);
  const xspan = Math.max(xmax - xmin, 1e-9), yspan = Math.max(ymax - ymin, 1e-9);
  const plot = usable.sort((a, b) => a.mjd - b.mjd).map(item => ({
    x: ((item.mjd - xmin) / xspan) * 900,
    y: 240 - ((item.mag - ymin) / yspan) * 200,
  }));
  const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
  group.setAttribute("class", "dynamic-light-curve");
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("class", "curve-line");
  path.setAttribute("d", plot.map((p, i) => (i ? "L" : "M") + p.x.toFixed(2) + " " + p.y.toFixed(2)).join(" "));
  group.appendChild(path);
  const points = document.createElementNS("http://www.w3.org/2000/svg", "g");
  points.setAttribute("class", "points");
  plot.forEach(point => {
    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", point.x.toFixed(2)); circle.setAttribute("cy", point.y.toFixed(2)); circle.setAttribute("r", "3");
    points.appendChild(circle);
  });
  group.appendChild(points); svg.appendChild(group);
}
async function loadObject() {
  setObjectIdentity();
  if (!state.oid) {
    setConnectionState("Object required", false);
    document.getElementById("viewSubtitle").textContent = "Provide ?oid=<object-id> to load scientific data";
    document.getElementById("resultState").textContent = "idle";
    return;
  }
  setConnectionState("Loading…");
  try {
    const result = await fetchJson("/v1/objects/" + encodeURIComponent(state.oid) +
      "/results/latest?survey=" + encodeURIComponent(state.survey));
    renderResult(result); setConnectionState("API ready"); return;
  } catch (error) {
    if (error.status !== 404) setConnectionState("API unavailable", false);
  }
  try {
    const payload = await fetchJson("/v1/objects/" + encodeURIComponent(state.oid) +
      "/observations?survey=" + encodeURIComponent(state.survey));
    state.observations = payload.observations || [];
    renderLightCurve(document.getElementById("lightCurveSvg"), state.observations);
    document.getElementById("viewSubtitle").textContent = "Live normalized observations · no durable result yet";
    document.getElementById("resultState").textContent = "observations only";
    setConnectionState("API ready");
  } catch {
    setConnectionState("API unavailable", false);
    document.getElementById("viewSubtitle").textContent = "Unable to load observations or durable results";
  }
}
async function runAnalysis() {
  const button = document.getElementById("runAnalysisButton");
  button.disabled = true; button.textContent = "Running…";
  try {
    const result = await fetchJson("/v1/objects/" + encodeURIComponent(state.oid) + "/analysis", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ survey: state.survey }),
    });
    renderResult({ schema_version: result.schema_version || "1.0", model_version: result.model_version, payload: result }, false);
    setConnectionState("Analysis complete");
  } catch { setConnectionState("Analysis failed", false); }
  finally { button.disabled = false; button.textContent = "Run analysis"; }
}
const mainCanvas = document.querySelector(".main-canvas");
const overviewMarkup = mainCanvas.innerHTML;

const titles = {
  overview: ["Object analysis", "Scientific overview"],
  observations: ["Observations", "Normalized observation stream"],
  dr24: ["DR24 Explorer", "Native DR24 light curve · raw data only"],
  features: ["Features", "Scientific Feature Engine output"],
  classification: ["Classification", "Model prediction and probabilities"],
  uncertainty: ["Uncertainty, OOD and anomaly", "Separate diagnostic outputs"],
  provenance: ["Provenance", "Traceable scientific metadata"],
  batch: ["Batch jobs", "Durable analysis jobs"],
  catalog: ["Catalog", "Catalog query and export module"],
  reports: ["Reports", "Scientific report generation module"],
  validation: ["Scientific Validation", "Release-blocking scientific evidence and provenance"],
  "desktop-home": ["Scientific Overview", "Live application state, saved analyses and scientific evidence"],
  workspaces: ["Workspaces", "Create and open workspaces"],
  sources: ["Data source", "Active source and retrieval contract"],
  "desktop-provenance": ["Provenance", "Retrieval metadata and evidence"],
  "desktop-export": ["Reports and exports", "Raw JSON export and reproducibility metadata"],
  "desktop-settings": ["Settings", "Local application settings"],
  "desktop-help": ["Help", "User guide and scientific scope"],
};

async function renderDesktopHome() {
  mainCanvas.innerHTML = [
    '<section class="mission-banner">',
      '<div class="mission-banner-copy">',
        '<div class="eyebrow">ZTF CLASSIFIER · SCIENTIFIC MISSION CONTROL</div>',
        '<h1 id="viewTitle">Scientific Overview</h1>',
        '<p id="viewSubtitle">Explore ZTF data, review saved analyses and monitor scientific evidence.</p>',
      '</div>',
      '<div class="mission-gate" id="missionGateBadge" data-state="warning">',
        '<span class="mission-gate-indicator"></span><span>SCIENTIFIC GATE: CHECKING</span>',
      '</div>',
    '</section>',
    '<section class="mission-metrics" aria-label="Platform summary">',
      '<article class="mission-metric metric-source"><span class="metric-icon" aria-hidden="true">◉</span><div><small>PRIMARY DATA SOURCE</small><strong>IRSA ZTF DR24</strong><span>Native light-curve records</span></div></article>',
      '<article class="mission-metric"><span class="metric-icon" aria-hidden="true">▣</span><div><small>ACTIVE WORKSPACES</small><strong id="missionWorkspaceCount">—</strong><span id="missionWorkspaceDetail">Checking local workspaces</span></div></article>',
      '<article class="mission-metric"><span class="metric-icon" aria-hidden="true">◈</span><div><small>SAVED ANALYSIS RESULTS</small><strong id="missionResultCount">—</strong><span>Durable result records</span></div></article>',
      '<article class="mission-metric metric-gate"><span class="metric-icon" aria-hidden="true">⚠</span><div><small>SCIENTIFIC VALIDATION</small><strong id="missionValidationStatus">CHECKING</strong><span id="missionValidationDetail">Fail-closed release gate</span></div></article>',
    '</section>',
    '<section class="mission-main-grid">',
      '<article class="mission-panel mission-lightcurve">',
        '<div class="mission-panel-header"><div><div class="mission-panel-title"><span class="panel-symbol">⌁</span>Light-curve workspace</div><div class="mission-panel-subtitle" id="missionCurveSubtitle">Latest saved scientific result · no demo data</div></div>',
          '<button class="mission-link-button" id="missionOpenCatalog" type="button">Result catalog <span aria-hidden="true">→</span></button>',
        '</div>',
        '<div class="mission-chart-wrap">',
          '<svg id="missionLightCurveSvg" viewBox="0 0 900 280" preserveAspectRatio="none" role="img" aria-label="Light curve from the latest saved scientific result">',
            '<g class="grid-lines"><line x1="0" y1="55" x2="900" y2="55"></line><line x1="0" y1="110" x2="900" y2="110"></line><line x1="0" y1="165" x2="900" y2="165"></line><line x1="0" y1="220" x2="900" y2="220"></line></g>',
          '</svg>',
          '<div class="axis-label x">MJD →</div><div class="axis-label y">mag</div>',
        '</div>',
        '<div class="mission-chart-footer"><span id="missionCurveObject">No saved light curve loaded.</span><span id="missionCurveCount">— observations</span></div>',
      '</article>',
      '<article class="mission-panel mission-status-panel">',
        '<div class="mission-panel-header"><div><div class="mission-panel-title"><span class="panel-symbol">⌁</span>Mission status</div><div class="mission-panel-subtitle">Live application and evidence state</div></div></div>',
        '<div id="missionStatusRows" class="mission-status-rows"><p class="muted">Reading application status…</p></div>',
        '<button class="mission-primary-button" id="missionViewValidation" type="button">View scientific validation <span aria-hidden="true">→</span></button>',
      '</article>',
    '</section>',
    '<section class="mission-bottom-grid">',
      '<article class="mission-panel">',
        '<div class="mission-panel-header"><div><div class="mission-panel-title"><span class="panel-symbol">✧</span>Analysis review</div><div class="mission-panel-subtitle">Persisted results available for review</div></div></div>',
        '<div id="missionReviewQueue" class="mission-list"><p class="muted">Loading saved results…</p></div>',
      '</article>',
      '<article class="mission-panel">',
        '<div class="mission-panel-header"><div><div class="mission-panel-title"><span class="panel-symbol">◷</span>Recent operations</div><div class="mission-panel-subtitle">Recorded asynchronous analysis jobs</div></div><button class="mission-link-button" id="missionOpenJobs" type="button">View all <span aria-hidden="true">→</span></button></div>',
        '<div id="missionRecentOperations" class="mission-list"><p class="muted">Loading analysis jobs…</p></div>',
      '</article>',
      '<article class="mission-panel mission-health-panel">',
        '<div class="mission-panel-header"><div><div class="mission-panel-title"><span class="panel-symbol">♡</span>System health</div><div class="mission-panel-subtitle">Checks reported by local services</div></div></div>',
        '<div id="missionHealthRows" class="mission-health-rows"><p class="muted">Checking local services…</p></div>',
      '</article>',
    '</section>',
    '<div class="mission-footer-note">Scientific data and status values come from the local API. Missing evidence remains visible and is never shown as PASS.</div>'
  ].join("");
  setViewHeading("desktop-home");

  document.getElementById("missionOpenCatalog").addEventListener("click", () => showView("catalog"));
  document.getElementById("missionOpenJobs").addEventListener("click", () => showView("batch"));
  document.getElementById("missionViewValidation").addEventListener("click", () => showView("validation"));

  const requests = await Promise.allSettled([
    fetchJson("/health"),
    fetchJson("/v1/workspaces"),
    fetchJson("/v1/workspaces/active"),
    fetchJson("/v1/model"),
    fetchJson("/v1/scientific-validation"),
    fetchJson("/v1/jobs?limit=5"),
    fetchJson("/v1/catalog/results?limit=8")
  ]);
  const valueAt = index => requests[index].status === "fulfilled" ? requests[index].value : null;
  const health = valueAt(0);
  const workspaceList = valueAt(1);
  const activeResponse = valueAt(2);
  const model = valueAt(3);
  const gate = valueAt(4);
  const jobsPage = valueAt(5);
  const catalog = valueAt(6);
  const activeWorkspace = activeResponse?.workspace || null;
  const lastOperation = activeWorkspace?.last_operation || null;
  const jobs = Array.isArray(jobsPage?.items) ? jobsPage.items : [];
  const results = Array.isArray(catalog?.items) ? catalog.items : [];

  const activeCount = Array.isArray(workspaceList?.items)
    ? workspaceList.items.filter(item => item.is_active).length
    : null;
  document.getElementById("missionWorkspaceCount").textContent =
    activeCount === null ? "—" : String(activeCount);
  document.getElementById("missionWorkspaceDetail").textContent =
    activeCount === null ? "Workspace service unavailable" :
      (activeWorkspace ? "Active: " + activeWorkspace.name : "No active workspace");
  document.getElementById("missionResultCount").textContent =
    catalog && Number.isInteger(catalog.total) ? String(catalog.total) : "—";

  const gateStatus = gate?.status || "UNAVAILABLE";
  document.getElementById("missionValidationStatus").textContent = gateStatus;
  document.getElementById("missionValidationDetail").textContent = gate
    ? String((gate.blockers || []).length) + " release blocker(s)"
    : "Validation service unavailable";
  const gateBadge = document.getElementById("missionGateBadge");
  gateBadge.dataset.state = gateStatus === "PASS" ? "good" : "warning";
  gateBadge.lastElementChild.textContent = "SCIENTIFIC GATE: " + gateStatus.replaceAll("_", " ");

  const retrievalStatus = !activeWorkspace ? "NO WORKSPACE" :
    !lastOperation ? "NOT RUN" : String(lastOperation.status || "UNKNOWN");
  const retrievalDetail = !activeWorkspace ? "Create or open a workspace" :
    !lastOperation ? "No DR24 request recorded" :
      "Last request: " + String(lastOperation.completed_at_utc || lastOperation.started_at_utc || "time unavailable");
  const modelStatus = model ? "REGISTERED" : "UNAVAILABLE";
  const modelDetail = model
    ? String(model.model_version || "Model version available")
    : "Model registry did not return an artifact";
  const apiHealthy = health?.status === "ok";
  if (apiHealthy) setConnectionState("Local API online", true);
  else setConnectionState("Local API unavailable", false);

  const statusRows = [
    ["Local API", apiHealthy ? "ONLINE" : "UNAVAILABLE", apiHealthy ? "good" : "danger"],
    ["DR24 acquisition", retrievalStatus, retrievalStatus === "SUCCEEDED" ? "good" : (retrievalStatus === "FAILED" || retrievalStatus === "INTERRUPTED" ? "danger" : "neutral")],
    ["Workspace", activeWorkspace ? "ACTIVE" : "NOT OPEN", activeWorkspace ? "good" : "warning"],
    ["Model registry", modelStatus, model ? "good" : "warning"],
    ["Scientific validation", gateStatus, gateStatus === "PASS" ? "good" : "warning"]
  ];
  document.getElementById("missionStatusRows").innerHTML = statusRows.map(row =>
    '<div class="mission-status-row"><span><i class="mission-status-icon ' + row[2] + '"></i>' +
    escapeHtml(row[0]) + '</span><strong class="mission-status-value ' + row[2] + '">' +
    escapeHtml(row[1]) + '</strong></div>'
  ).join("");

  document.getElementById("missionHealthRows").innerHTML = [
    '<div class="mission-health-row"><span>Application API</span><strong class="' + (apiHealthy ? "good" : "danger") + '">' + (apiHealthy ? "Healthy" : "Unavailable") + '</strong></div>',
    '<div class="mission-health-row"><span>Workspace service</span><strong class="' + (workspaceList && activeResponse ? "good" : "warning") + '">' + (workspaceList && activeResponse ? "Available" : "Not verified") + '</strong></div>',
    '<div class="mission-health-row"><span>Model registry</span><strong class="' + (model ? "good" : "warning") + '">' + (model ? "Available" : "Not available") + '</strong></div>',
    '<div class="mission-health-row"><span>Scientific gate</span><strong class="' + (gateStatus === "PASS" ? "good" : "warning") + '">' + escapeHtml(gateStatus) + '</strong></div>'
  ].join("");

  const jobsContainer = document.getElementById("missionRecentOperations");
  if (!jobsPage) {
    jobsContainer.innerHTML = '<p class="muted">Analysis job service is unavailable.</p>';
  } else if (!jobs.length) {
    jobsContainer.innerHTML = '<p class="mission-empty">No analysis jobs have been recorded.</p>';
  } else {
    jobsContainer.innerHTML = jobs.slice(0, 5).map(job =>
      '<div class="mission-operation-row"><span class="mission-operation-dot ' +
      (String(job.status).toLowerCase() === "succeeded" ? "good" :
        (String(job.status).toLowerCase() === "failed" ? "danger" : "neutral")) +
      '"></span><div class="mission-operation-copy"><strong>' + escapeHtml(job.oid) +
      '</strong><span>' + escapeHtml(job.status) + ' · ' + escapeHtml(job.updated_at || job.created_at || "time unavailable") +
      '</span></div></div>'
    ).join("");
  }

  const reviewQueue = document.getElementById("missionReviewQueue");
  if (!catalog) {
    reviewQueue.innerHTML = '<p class="muted">Saved result catalog is unavailable.</p>';
  } else if (!results.length) {
    reviewQueue.innerHTML = '<p class="mission-empty">No saved scientific results are available yet. Results will appear here after a completed analysis.</p>';
  } else {
    reviewQueue.innerHTML = results.slice(0, 5).map(item => {
      const predicted = item.payload?.prediction?.predicted_class || "No prediction field";
      return '<button class="mission-review-item" type="button" data-mission-result="' +
        escapeHtml(item.result_id) + '"><span class="mission-review-oid">' +
        escapeHtml(item.oid) + '</span><span class="mission-review-class">' +
        escapeHtml(predicted) + '</span><span class="mission-review-date">' +
        escapeHtml(item.created_at || "time unavailable") + '</span><span aria-hidden="true">→</span></button>';
    }).join("");
    reviewQueue.querySelectorAll("[data-mission-result]").forEach(button => {
      button.addEventListener("click", async () => {
        button.disabled = true;
        try {
          const record = await fetchJson("/v1/results/" + encodeURIComponent(button.dataset.missionResult));
          state.result = record;
          state.oid = record.oid;
          await showView("overview", { result: record });
        } catch {
          setConnectionState("Saved result could not be opened", false);
          button.disabled = false;
        }
      });
    });
  }

  const chartResult = results.find(item =>
    Array.isArray(item.payload?.observations) && item.payload.observations.length > 0
  );
  const chartSvg = document.getElementById("missionLightCurveSvg");
  if (chartResult) {
    renderLightCurve(chartSvg, chartResult.payload.observations);
    document.getElementById("missionCurveObject").textContent =
      "Object " + chartResult.oid + " · saved result";
    document.getElementById("missionCurveCount").textContent =
      String(chartResult.payload.observations.length) + " observations";
    document.getElementById("missionCurveSubtitle").textContent =
      "Latest available saved result · normalized observation data";
  } else {
    renderLightCurve(chartSvg, []);
    document.getElementById("missionCurveObject").textContent =
      "No saved result contains light-curve observations.";
    document.getElementById("missionCurveCount").textContent = "No data";
  }

  if (!workspaceList && !activeResponse && !model && !gate && !jobsPage && !catalog && !health) {
    setConnectionState("Local services unavailable", false);
  }
}

function renderDesktopSources() {
  mainCanvas.innerHTML = `
    <div class="canvas-header"><div><div class="eyebrow">DATA SOURCE</div><h1 id="viewTitle"></h1><p id="viewSubtitle"></p></div></div>
    <section class="panel">
      <div class="panel-title">IRSA ZTF DR24 Lightcurves HATS</div>
      <div class="panel-subtitle">Active preview source</div>
      <dl class="metadata">
        <div><dt>Release</dt><dd>DR24</dd></div>
        <div><dt>Search index</dt><dd>objectid</dd></div>
        <div><dt>Filters</dt><dd>g / r / i</dd></div>
        <div><dt>Request limit</dt><dd>1–10 OIDs</dd></div>
        <div><dt>Network requirement</dt><dd>Internet connection required</dd></div>
        <div><dt>Fallback source</dt><dd>Not used</dd></div>
      </dl>
    </section>
    <section class="panel">
      <div class="panel-title">Data contract</div>
      <ul>
        <li>Raw time is preserved in the HMJD column; HMJD is not the same as MJD.</li>
        <li>Native ZTF magnitude and magnitude error are preserved.</li>
        <li>catflags are preserved; no masking or row removal is applied.</li>
        <li>Each OID remains a separate record; no physical-source grouping is performed.</li>
      </ul>
    </section>`;
  setViewHeading("sources");
}

async function renderDesktopWorkspaces() {
  mainCanvas.innerHTML = `
    <div class="canvas-header"><div><div class="eyebrow">WORKSPACES</div><h1 id="viewTitle"></h1><p id="viewSubtitle"></p></div></div>
    <section class="panel">
      <div class="panel-title">Create workspace</div>
      <p class="muted">Each workspace stores its operation history and exports in the app's user-data directory.</p>
      <form id="workspaceCreateForm" class="workspace-create-form">
        <label for="workspaceName">Workspace name</label>
        <input id="workspaceName" name="name" type="text" maxlength="64" required placeholder="e.g. Transient-object review">
        <button class="primary-button" type="submit">Create workspace</button>
      </form>
      <p id="workspaceStatus" class="muted" role="status">Loading workspaces…</p>
    </section>
    <section class="panel">
      <div class="panel-title">Saved workspaces</div>
      <div id="workspaceList" class="workspace-list"></div>
    </section>`;
  setViewHeading("workspaces");

  const status = document.getElementById("workspaceStatus");
  const list = document.getElementById("workspaceList");
  const form = document.getElementById("workspaceCreateForm");
  const nameInput = document.getElementById("workspaceName");

  async function refreshWorkspaces() {
    const payload = await fetchJson("/v1/workspaces");
    const items = Array.isArray(payload.items) ? payload.items : [];
    if (!items.length) {
      list.innerHTML = '<p class="muted">No workspaces created yet.</p>';
    } else {
      list.innerHTML = items.map(item => {
        const active = item.is_active;
        const label = active ? "Active" : item.status === "CORRUPT" ? "Needs review" : "Saved";
        const operation = item.last_operation;
        const operationText = operation
          ? operation.status + " · " + (operation.returned_oids || []).length +
            "/" + (operation.requested_oids || []).length + " OID"
          : "No operations recorded yet";
        const exportText = item.last_export
          ? "Last export: " + item.last_export.file_name
          : "No export saved yet";
        return `
          <article class="workspace-list-item">
            <div>
              <strong>${escapeHtml(item.name)}</strong>
              <small>${escapeHtml(label)} · ${escapeHtml(item.created_at_utc || "")}</small>
              <small>Last operation: ${escapeHtml(operationText)}</small>
              <small>${escapeHtml(exportText)}</small>
            </div>
            <div class="workspace-actions">
              <button class="text-button" type="button" data-open-workspace="${escapeHtml(item.workspace_id)}" ${active ? "disabled" : ""}>${active ? "Active workspace" : "Open"}</button>
              ${item.last_export ? '<button class="text-button" type="button" data-restore-export="' + escapeHtml(item.workspace_id) + '" data-export-file="' + escapeHtml(item.last_export.file_name) + '">Restore export</button>' : ""}
            </div>
          </article>`;
      }).join("");
      list.querySelectorAll("[data-open-workspace]").forEach(button => {
        button.addEventListener("click", async () => {
          button.disabled = true;
          try {
            await fetchJson("/v1/workspaces/" + encodeURIComponent(button.dataset.openWorkspace) + "/open", { method: "POST" });
            desktopRawExport = null;
            desktopDr24Payload = null;
            desktopRawExportPersisted = false;
            status.textContent = "Workspace opened and set as active.";
            await refreshWorkspaces();
          } catch (error) {
            status.textContent = "Could not open workspace: " + (error.message || "Unknown error");
            button.disabled = false;
          }
        });
      });
      list.querySelectorAll("[data-restore-export]").forEach(button => {
        button.addEventListener("click", async () => {
          button.disabled = true;
          try {
            const workspaceId = button.dataset.restoreExport;
            const activeWorkspace = await fetchJson("/v1/workspaces/active");
            if (activeWorkspace.workspace?.workspace_id !== workspaceId) {
              await fetchJson("/v1/workspaces/" + encodeURIComponent(workspaceId) + "/open", { method: "POST" });
            }
            const restored = await fetchJson(
              "/v1/workspaces/exports/" + encodeURIComponent(button.dataset.exportFile)
            );
            desktopRawExport = restored;
            desktopDr24Payload = restored.source_payload || null;
            desktopRawExportPersisted = true;
            status.textContent = "Latest export restored from workspace.";
            showView("desktop-export");
          } catch (error) {
            status.textContent = "Could not restore export: " + (error.message || "Unknown error");
            button.disabled = false;
          }
        });
      });
    }
    status.textContent = items.length + " saved workspaces · active workspace: " + (payload.active_workspace_id || "None");
  }

  form.addEventListener("submit", async event => {
    event.preventDefault();
    const name = nameInput.value.trim();
    if (!name) return;
    const submit = form.querySelector("button[type=submit]");
    submit.disabled = true;
    try {
      await fetchJson("/v1/workspaces", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name })
      });
      desktopRawExport = null;
      desktopDr24Payload = null;
      desktopRawExportPersisted = false;
      nameInput.value = "";
      status.textContent = "Workspace created.";
      await refreshWorkspaces();
    } catch (error) {
      status.textContent = "Could not create workspace: " + (error.message || "Unknown error");
    } finally {
      submit.disabled = false;
    }
  });

  try {
    await refreshWorkspaces();
  } catch (error) {
    status.textContent = "Could not load workspaces: " + (error.message || "Unknown error");
  }
}

function renderDesktopProvenance() {
  const provenance = desktopDr24Payload?.provenance;
  mainCanvas.innerHTML = `
    <div class="canvas-header"><div><div class="eyebrow">PROVENANCE</div><h1 id="viewTitle"></h1><p id="viewSubtitle"></p></div></div>
    <section class="panel">
      <div class="panel-title">Provenance status</div>
      <p class="muted">${provenance ? "Data was retrieved from the DR24 source." : "NOT RUN · No data retrieval has been performed."}</p>
      <pre class="report-content" id="desktopProvenanceJson">${provenance ? escapeHtml(JSON.stringify(provenance, null, 2)) : "NOT RUN"}</pre>
    </section>`;
  setViewHeading("desktop-provenance");
}

async function downloadDesktopRawExport() {
  if (!desktopRawExport) {
    setConnectionState("No DR24 export available", false);
    return;
  }
  const button = document.getElementById("desktopDownloadJson") ||
    document.getElementById("dr24ExportButton");
  if (button) button.disabled = true;
  try {
    let metadata = null;
    if (!desktopRawExportPersisted) {
      metadata = await fetchJson("/v1/workspaces/exports", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(desktopRawExport)
      });
      desktopRawExportPersisted = true;
    }
    const blob = new Blob([JSON.stringify(desktopRawExport, null, 2)], {
      type: "application/json"
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    const ids = desktopRawExport.source_payload?.provenance?.requested_oids || [];
    link.download = "ztf-dr24-batch-" + ids.join("_") + "-raw-export.json";
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    setConnectionState(metadata
      ? "Export saved to active workspace · SHA-256 " + metadata.sha256.slice(0, 12)
      : "Restored workspace export downloaded");
  } catch (error) {
    setConnectionState("Workspace export failed (" + (error.status || "storage") + ")", false);
    const status = document.getElementById("dr24Status");
    if (status) status.textContent = "Could not save the export to the active workspace. The file was not downloaded.";
  } finally {
    if (button) button.disabled = false;
  }
}

function renderDesktopExport() {
  const available = Boolean(desktopRawExport);
  const provenance = desktopDr24Payload?.provenance || {};
  mainCanvas.innerHTML = `
    <div class="canvas-header"><div><div class="eyebrow">EXPORT</div><h1 id="viewTitle"></h1><p id="viewSubtitle"></p></div></div>
    <section class="panel">
      <div class="panel-title">Raw JSON export</div>
      <p class="muted">${available ? "Ready to download" : "NOT RUN · Retrieve DR24 data first."}</p>
      <dl class="metadata">
        <div><dt>Export schema</dt><dd>${available ? "ztf-dr24-raw-export-v0.3" : "—"}</dd></div>
        <div><dt>Requested OIDs</dt><dd>${escapeHtml((provenance.requested_oids || []).join(", ") || "—")}</dd></div>
        <div><dt>Returned OIDs</dt><dd>${escapeHtml((provenance.returned_oids || []).join(", ") || "—")}</dd></div>
        <div><dt>Missing OIDs</dt><dd>${escapeHtml((provenance.missing_oids || []).join(", ") || "—")}</dd></div>
      </dl>
      <button class="primary-button" id="desktopDownloadJson" type="button" ${available ? "" : "disabled"}>Download JSON file</button>
    </section>`;
  setViewHeading("desktop-export");
  const button = document.getElementById("desktopDownloadJson");
  button.addEventListener("click", downloadDesktopRawExport);
}

async function renderDesktopSettings() {
  mainCanvas.innerHTML = `
    <div class="canvas-header"><div><div class="eyebrow">SETTINGS</div><h1 id="viewTitle"></h1><p id="viewSubtitle"></p></div></div>
    <section class="panel">
      <div class="panel-title">Display settings</div>
      <p>Use the settings button in the application header to change the theme.</p>
      <p class="muted">Settings and workspace files are stored in the Windows user-data directory. Uninstalling the app does not delete user data.</p>
    </section>
    <section class="panel">
      <div class="panel-title">Connection status</div>
      <p id="desktopSettingsStatus" class="muted">Checking local service…</p>
    </section>`;
  setViewHeading("desktop-settings");
  const status = document.getElementById("desktopSettingsStatus");
  try {
    await fetchJson("/v1/settings");
    status.textContent = "Local service is available.";
  } catch {
    status.textContent = "Local service is unavailable.";
  }
}

function renderDesktopHelp() {
  mainCanvas.innerHTML = `
    <div class="canvas-header"><div><div class="eyebrow">HELP & ABOUT</div><h1 id="viewTitle"></h1><p id="viewSubtitle"></p></div></div>
    <section class="panel">
      <div class="panel-title">Quick guide</div>
      <ol>
        <li>Create or open a workspace from the Workspaces page. DR24 retrieval does not start without an active workspace.</li>
        <li>Open the DR24 Explorer.</li>
        <li>Enter one to ten positive ZTF object IDs.</li>
        <li>Run the retrieval and review the request status. A missing workspace is a preflight requirement, not a DR24 source failure.</li>
        <li>Review the native light curve, raw observation table, diagnostic QC and descriptive statistics.</li>
        <li>Review acquisition provenance and download the raw JSON + QC export.</li>
      </ol>
    </section>
    <section class="panel">
      <div class="panel-title">Limitations</div>
      <ul>
        <li>Live retrieval requires an internet connection.</li>
        <li>QC in this preview is diagnostic and is not production-approved.</li>
        <li>Descriptive statistics are not model features.</li>
        <li>Classification and anomaly detection are not run in this preview.</li>
        <li>An OID is a catalog identifier. It does not prove physical-source identity.</li>
      </ul>
    </section>`;
  setViewHeading("desktop-help");
}

function setViewHeading(view) {
  const heading = document.getElementById("viewTitle");
  const subtitle = document.getElementById("viewSubtitle");
  heading.textContent = desktopTranslate(
    view === "overview" ? (state.oid || "Select an object") : titles[view][0]
  );
  subtitle.textContent = desktopTranslate(titles[view][1]);
}

function bindOverviewActions() {
  const runButton = document.getElementById("runAnalysisButton");
  const exportButton = document.getElementById("exportReportButton");
  if (runButton) runButton.addEventListener("click", runAnalysis);
  if (exportButton) exportButton.addEventListener("click", exportCurrentReport);
}

async function exportCurrentReport() {
  if (!state.result || !state.result.result_id) {
    setConnectionState("No durable result to export", false);
    return;
  }
  try {
    const response = await fetch(
      "/v1/results/" + encodeURIComponent(state.result.result_id) + "/report",
      { headers: { Accept: "text/markdown" } },
    );
    if (!response.ok) throw new Error("HTTP " + response.status);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "ztf-analysis-" + state.result.result_id + ".md";
    link.click();
    URL.revokeObjectURL(url);
    setConnectionState("Report ready");
  } catch {
    setConnectionState("Report export failed", false);
  }
}

function renderCatalogShell() {
  mainCanvas.innerHTML = `
    <div class="canvas-header">
      <div><div class="eyebrow">SCIENTIFIC CATALOG</div><h1 id="viewTitle">Catalog</h1>
      <p id="viewSubtitle">Persisted scientific results</p></div>
      <div class="object-actions"><button class="secondary-button" id="catalogExport">Export CSV</button></div>
    </div>
    <section class="panel"><div class="panel-header"><div>
      <div class="panel-title">Durable results</div><div class="panel-subtitle" id="catalogSummary">Loading…</div>
    </div></div>
    <div class="catalog-table-wrap"><table class="metadata"><thead><tr>
      <th>Object</th><th>Survey</th><th>Model</th><th>Prediction</th><th>Created</th><th>Result</th>
    </tr></thead><tbody id="catalogRows"></tbody></table></div></section>`;
}

async function loadCatalog() {
  renderCatalogShell();
  try {
    const page = await fetchJson("/v1/catalog/results?limit=100");
    document.getElementById("catalogSummary").textContent =
      page.total + " persisted result(s)" + (page.has_next ? " · more available" : "");
    const rows = document.getElementById("catalogRows");
    rows.innerHTML = page.items.map(item => {
      const prediction = item.payload?.prediction?.predicted_class || "—";
      return "<tr><td>" + escapeHtml(item.oid) + "</td><td>" +
        escapeHtml(item.survey) + "</td><td>" + escapeHtml(item.model_version) +
        "</td><td>" + escapeHtml(prediction) + "</td><td>" +
        escapeHtml(item.created_at) + "</td><td><button class=\"text-button\" data-result-id=\"" +
        escapeHtml(item.result_id) + "\">Open</button></td></tr>";
    }).join("") || '<tr><td colspan="6">No durable results.</td></tr>';
    rows.querySelectorAll("[data-result-id]").forEach(button => {
      button.addEventListener("click", async () => {
        const record = await fetchJson("/v1/results/" + encodeURIComponent(button.dataset.resultId));
        state.result = record;
        state.oid = record.oid;
        showView("overview");
      });
    });
    document.getElementById("catalogExport").addEventListener("click", () => {
      window.location.href = "/v1/catalog/results.csv?limit=1000";
    });
    setConnectionState("Catalog ready");
  } catch {
    setConnectionState("Catalog unavailable", false);
  }
}

async function loadBatchJobs() {
  mainCanvas.innerHTML = `
    <div class="canvas-header"><div><div class="eyebrow">WORKSPACE</div><h1 id="viewTitle">Batch jobs</h1>
    <p id="viewSubtitle">Durable asynchronous analysis jobs</p></div></div>
    <section class="panel"><div class="panel-header"><div>
      <div class="panel-title">Job queue</div><div class="panel-subtitle" id="jobsSummary">Loading…</div>
    </div></div><div class="catalog-table-wrap"><table class="metadata"><thead><tr>
      <th>Object</th><th>Status</th><th>Model</th><th>Updated</th><th>Result</th>
    </tr></thead><tbody id="jobRows"></tbody></table></div></section>`;
  try {
    const page = await fetchJson("/v1/jobs?limit=100");
    document.getElementById("jobsSummary").textContent = page.items.length + " recent job(s)";
    const rows = document.getElementById("jobRows");
    rows.innerHTML = page.items.map(job =>
      "<tr><td>" + escapeHtml(job.oid) + "</td><td>" + escapeHtml(job.status) +
      "</td><td>" + escapeHtml(job.model_version || "default") + "</td><td>" +
      escapeHtml(job.updated_at) + "</td><td>" +
      (job.scientific_result_id
        ? '<button class="text-button" data-job-result="' + escapeHtml(job.scientific_result_id) + '">Open result</button>'
        : "—") + "</td></tr>"
    ).join("") || '<tr><td colspan="5">No jobs.</td></tr>';
    rows.querySelectorAll("[data-job-result]").forEach(button => {
      button.addEventListener("click", async () => {
        state.result = await fetchJson("/v1/results/" + encodeURIComponent(button.dataset.jobResult));
        state.oid = state.result.oid;
        showView("overview");
      });
    });
    setConnectionState("Jobs ready");
  } catch {
    setConnectionState("Jobs unavailable", false);
  }
}

async function loadReportView() {
  mainCanvas.innerHTML = `
    <div class="canvas-header"><div><div class="eyebrow">SCIENTIFIC REPORT</div><h1 id="viewTitle">Report</h1>
    <p id="viewSubtitle">Deterministic report from a durable scientific result</p></div>
    <div class="object-actions"><button class="primary-button" id="reportDownload">Export Markdown</button></div></div>
    <section class="panel"><pre id="reportContent" class="report-content">Loading…</pre></section>`;
  if (!state.result?.result_id) {
    document.getElementById("reportContent").textContent = "Select a durable result from Catalog or Batch jobs first.";
    document.getElementById("reportDownload").disabled = true;
    return;
  }
  try {
    const response = await fetch("/v1/results/" + encodeURIComponent(state.result.result_id) + "/report");
    if (!response.ok) throw new Error("HTTP " + response.status);
    const markdown = await response.text();
    document.getElementById("reportContent").textContent = markdown;
    document.getElementById("reportDownload").addEventListener("click", exportCurrentReport);
    setConnectionState("Report ready");
  } catch {
    document.getElementById("reportContent").textContent = "Report unavailable.";
    setConnectionState("Report unavailable", false);
  }
}

function renderAnalysisModule(view) {
  mainCanvas.innerHTML = `
    <div class="canvas-header"><div><div class="eyebrow">SCIENTIFIC ANALYSIS</div><h1 id="viewTitle"></h1>
    <p id="viewSubtitle"></p></div></div>
    <section class="panel"><div id="moduleContent"></div></section>`;
  setViewHeading(view);
  const payload = state.result?.payload || {};
  const target = document.getElementById("moduleContent");
  if (view === "observations") {
    const observations = payload.observations || state.observations;
    target.innerHTML = "<h2>Normalized observations</h2><p>" + observations.length +
      " observation(s) available.</p><pre>" + escapeHtml(JSON.stringify(observations, null, 2)) + "</pre>";
  } else if (view === "features") {
    target.innerHTML = "<h2>Scientific features</h2><p>" +
      Object.keys(payload.features || {}).length + " feature(s).</p><pre>" +
      escapeHtml(JSON.stringify(payload.features || {}, null, 2)) + "</pre>";
  } else if (view === "classification") {
    target.innerHTML = "<h2>Classification</h2><pre>" +
      escapeHtml(JSON.stringify(payload.prediction || {}, null, 2)) + "</pre>";
  } else if (view === "uncertainty") {
    target.innerHTML = "<h2>Uncertainty and OOD diagnostics</h2><pre>" +
      escapeHtml(JSON.stringify({
        conformal: payload.prediction?.conformal || [],
        ood: payload.prediction?.ood || null,
        scientific_anomaly: payload.prediction?.scientific_anomaly || null,
        diagnostics: payload.diagnostics || {},
      }, null, 2)) + "</pre>";
  } else {
    target.innerHTML = "<h2>Provenance</h2><pre>" +
      escapeHtml(JSON.stringify({
        observation: payload.observation_provenance || {},
        feature: payload.feature_provenance || {},
        model: payload.model_provenance || {},
      }, null, 2)) + "</pre>";
  }
}

async function loadValidationDashboard() {
  mainCanvas.innerHTML = `
    <div class="canvas-header"><div><div class="eyebrow">RELEASE GATE</div><h1 id="viewTitle">Scientific Validation</h1>
    <p id="viewSubtitle">Independent evidence status · fail-closed release boundary</p></div></div>
    <section class="metric-grid">
      <article class="metric-card"><span>Gate status</span><strong id="validationStatus">—</strong><small>release-blocking</small></article>
      <article class="metric-card"><span>Benchmarks</span><strong id="validationBenchmarks">—</strong><small>registered sources</small></article>
      <article class="metric-card"><span>Blocked checks</span><strong id="validationBlockers">—</strong><small>must reach zero for release</small></article>
      <article class="metric-card"><span>Probe</span><strong id="validationProbe">—</strong><small>source provenance evidence</small></article>
    </section>
    <section class="panel"><div class="panel-header"><div><div class="panel-title">Benchmark gate</div><div class="panel-subtitle">No missing evidence is silently treated as PASS</div></div></div>
    <div class="catalog-table-wrap"><table class="metadata"><thead><tr><th>Benchmark</th><th>Role</th><th>Status</th><th>Blockers</th></tr></thead><tbody id="validationRows"></tbody></table></div></section>
    <section class="panel"><div class="panel-header"><div><div class="panel-title">Source provenance</div><div class="panel-subtitle">Reachability is provenance evidence, not scientific validation</div></div></div>
    <pre id="validationProbeDetails" class="report-content"></pre></section>`;
  try {
    const payload = await fetchJson("/v1/scientific-validation");
    document.getElementById("validationStatus").textContent = payload.status;
    document.getElementById("validationBenchmarks").textContent = payload.benchmarks.length;
    document.getElementById("validationBlockers").textContent = payload.blockers.length;
    const probe = payload.source_probe;
    const probeItems = probe?.sources || [];
    const reachable = probeItems.filter(item => item.status === "REACHABLE").length;
    document.getElementById("validationProbe").textContent = probe ? reachable + "/" + probeItems.length : "not run";
    document.getElementById("validationRows").innerHTML = payload.benchmarks.map(item =>
      "<tr><td>" + escapeHtml(item.benchmark_id) + "</td><td>" +
      escapeHtml(item.evaluation_role) + "</td><td>" + escapeHtml(item.status) +
      "</td><td>" + escapeHtml(item.blockers.join("; ") || "—") + "</td></tr>"
    ).join("");
    document.getElementById("validationProbeDetails").textContent =
      JSON.stringify({ interpretation: payload.interpretation, source_probe: probe }, null, 2);
    setConnectionState(payload.status === "PASS" ? "Scientific gate PASS" : "Scientific gate blocked", payload.status === "PASS");
  } catch {
    setConnectionState("Scientific validation unavailable", false);
  }
}


async function loadDR24Explorer() {
  mainCanvas.innerHTML = [
    '<div class="canvas-header"><div><div class="eyebrow">SOURCE EXPLORER · EXPERIMENTAL</div>',
    '<h1 id="viewTitle">DR24 Explorer</h1>',
    '<p id="viewSubtitle">Native DR24 data only. No feature normalization or model inference.</p></div></div>',
    '<section class="panel"><div class="panel-header"><div><div class="panel-title">Indexed multi-OID lookup</div>',
    '<div class="panel-subtitle">Enter 1–10 positive ZTF DR24 object IDs. Separate OIDs remain separate records; no broad catalog scan is performed.</div></div></div>',
    '<div style="display:flex;gap:12px;align-items:end;flex-wrap:wrap;padding:12px 0">',
    '<label for="dr24ObjectIds">DR24 object IDs</label>',
    '<textarea id="dr24ObjectIds" rows="3" placeholder="One or more OIDs, separated by commas or spaces" style="min-width:min(100%,520px)"></textarea>',
    desktopMode ? '<button class="secondary-button" id="dr24SampleButton" type="button">Tested sample OIDs</button><small class="muted">These two sample OIDs are separate records.</small>' : '',
    '<button class="primary-button" id="dr24LoadButton" type="button">Load raw light curves</button>',
    '<button id="dr24ExportButton" type="button" disabled>Download raw JSON + QC</button>',
    '</div><p id="dr24Status" class="muted" role="status">No DR24 objects loaded.</p></section>',
    '<div id="dr24Results"><section class="panel muted">Enter up to 10 OIDs to inspect native DR24 records.</section></div>',
    '<section class="panel"><div class="panel-header"><div><div class="panel-title">Acquisition provenance</div>',
    '<div class="panel-subtitle">Source, schema, query, missing OIDs and payload hashes</div></div></div>',
    '<pre id="dr24Provenance" class="report-content">No acquisition performed.</pre></section>'
  ].join("");
  setViewHeading("dr24");
  translateDesktopText(mainCanvas);
  desktopDr24Payload = null;
  desktopRawExport = null;
  const input = document.getElementById("dr24ObjectIds");
  const loadButton = document.getElementById("dr24LoadButton");
  const exportButton = document.getElementById("dr24ExportButton");
  let lastRawExport = null;
  const initialIds = params.get("objectids") || params.get("objectid") || "";
  if (initialIds) input.value = initialIds;
  const sampleButton = document.getElementById("dr24SampleButton");
  if (sampleButton) {
    sampleButton.addEventListener("click", () => {
      input.value = "264114400013085, 264214400000912";
    });
  }

  function parseObjectIds(value) {
    const tokens = value.split(/[\s,;]+/).filter(Boolean);
    if (tokens.length < 1 || tokens.length > 10) {
      throw new Error("Enter between 1 and 10 object IDs.");
    }
    if (tokens.some(token => !/^[1-9][0-9]*$/.test(token))) {
      throw new Error("Every object ID must be a positive integer.");
    }
    const ids = tokens.map(Number);
    if (ids.some(id => !Number.isSafeInteger(id) || id <= 0)) {
      throw new Error("Every object ID must be a safe positive integer.");
    }
    if (new Set(ids).size !== ids.length) {
      throw new Error("Duplicate object IDs are not allowed.");
    }
    return ids;
  }

  function renderRecord(record, qc, summaryEntry) {
    const oid = Number(record.objectid);
    const summary = summaryEntry && summaryEntry.summary ? summaryEntry.summary : {};
    const stat = (value, digits = 3) =>
      typeof value === "number" && Number.isFinite(value) ? value.toFixed(digits) : "—";
    const summaryPanel = [
      '<div class="panel-title" style="margin-top:18px">Descriptive time-series summary</div>',
      '<div class="panel-subtitle">Source-native descriptive statistics · not model features or classification</div>',
      '<div class="metadata-grid">',
      '<div><span>Finite HMJD/mag pairs</span><strong>', escapeHtml(summary.finite_hmjd_mag_pair_count ?? "—"), '</strong></div>',
      '<div><span>HMJD span (days)</span><strong>', escapeHtml(stat(summary.hmjd_span_days, 2)), '</strong></div>',
      '<div><span>Median sampling interval (days)</span><strong>', escapeHtml(stat(summary.median_sampling_interval_days, 3)), '</strong></div>',
      '<div><span>Median magnitude</span><strong>', escapeHtml(stat(summary.mag_median, 3)), '</strong></div>',
      '<div><span>Magnitude P05–P95 range</span><strong>', escapeHtml(stat(summary.mag_p05, 3)), ' – ', escapeHtml(stat(summary.mag_p95, 3)), '</strong></div>',
      '<div><span>Median non-negative magerr</span><strong>', escapeHtml(stat(summary.magerr_median, 4)), '</strong></div>',
      '</div>',
      '<p class="muted">All finite HMJD/magnitude pairs are included, regardless of catflags. No epoch filtering, time conversion, photometry conversion, OID grouping, feature generation, or inference was performed.</p>'
    ].join("");
    const filterName = ({1:"g",2:"r",3:"i"})[record.filterid] || "unknown";
    const epochs = Array.isArray(record.epochs) ? record.epochs : [];
    // Keep missing or non-numeric source values out of the chart. In particular,
    // Number(null) is zero and must not turn a missing HMJD/magnitude into a point.
    const points = epochs.filter(epoch =>
      typeof epoch.hmjd === "number" && Number.isFinite(epoch.hmjd) &&
      typeof epoch.mag === "number" && Number.isFinite(epoch.mag)
    ).map(epoch => ({
      x: epoch.hmjd,
      y: epoch.mag,
      magerr: epoch.magerr,
      flags: epoch.catflags
    }));
    let chart = "";
    if (points.length) {
      let xmin = Infinity, xmax = -Infinity, ymin = Infinity, ymax = -Infinity;
      for (const point of points) {
        xmin = Math.min(xmin, point.x);
        xmax = Math.max(xmax, point.x);
        const hasError = typeof point.magerr === "number" &&
          Number.isFinite(point.magerr) && point.magerr >= 0;
        const error = hasError ? point.magerr : 0;
        ymin = Math.min(ymin, point.y - error);
        ymax = Math.max(ymax, point.y + error);
      }
      const xspan = xmax - xmin || 1, yspan = ymax - ymin || 1;
      const errorBars = points.map(point => {
        if (typeof point.magerr !== "number" ||
            !Number.isFinite(point.magerr) || point.magerr < 0) return "";
        const x = 35 + ((point.x - xmin) / xspan) * 830;
        const y1 = 18 + ((point.y - point.magerr - ymin) / yspan) * 235;
        const y2 = 18 + ((point.y + point.magerr - ymin) / yspan) * 235;
        return '<line class="dr24-error-bar" x1="' + x.toFixed(2) +
          '" x2="' + x.toFixed(2) + '" y1="' + y1.toFixed(2) +
          '" y2="' + y2.toFixed(2) +
          '" stroke="#aebdce" stroke-width="1.5"><title>magerr ' +
          escapeHtml(point.magerr) + '</title></line>';
      }).join("");
      const circles = points.map(point => {
        const x = 35 + ((point.x - xmin) / xspan) * 830;
        const y = 18 + ((point.y - ymin) / yspan) * 235;
        const flagsKnown = typeof point.flags === "number" &&
          Number.isInteger(point.flags) && point.flags >= 0;
        const flagged = flagsKnown && (point.flags & 32768) !== 0;
        const fill = !flagsKnown ? "#9aa4b2" : (flagged ? "#e0a34a" : "#55b8df");
        return '<circle cx="' + x.toFixed(2) + '" cy="' + y.toFixed(2) +
          '" r="3" fill="' + fill + '" fill-opacity="0.85"><title>HMJD ' +
          escapeHtml(point.x) + ', mag ' + escapeHtml(point.y) +
          ', magerr ' + escapeHtml(point.magerr) + ', catflags ' +
          escapeHtml(point.flags) + '</title></circle>';
      }).join("");
      chart = '<div class="chart" style="margin-top:12px"><svg viewBox="0 0 900 280" ' +
        'preserveAspectRatio="none" role="img" aria-label="DR24 light curve for OID ' +
        oid + '"><g class="grid-lines"><line x1="0" y1="55" x2="900" y2="55"/>' +
        '<line x1="0" y1="110" x2="900" y2="110"/><line x1="0" y1="165" x2="900" y2="165"/>' +
        '<line x1="0" y1="220" x2="900" y2="220"/></g>' +
        errorBars + circles + '</svg>' +
        '<div class="axis-label x">HMJD (HJD − 2400000.5) →</div>' +
        '<div class="axis-label y">mag</div></div>';
    } else {
      chart = '<p class="muted">No finite numeric HMJD/magnitude pairs are available to plot. Raw rows remain available below and in the JSON export.</p>';
    }
    const tableRows = epochs.slice(0, 50).map(epoch =>
      "<tr><td>" + escapeHtml(epoch.hmjd) + "</td><td>" + escapeHtml(epoch.mag) +
      "</td><td>" + escapeHtml(epoch.magerr) + "</td><td>" + escapeHtml(epoch.clrcoeff) +
      "</td><td>" + escapeHtml(epoch.catflags) + "</td></tr>"
    ).join("");
    const qcText = qc ? JSON.stringify(qc, null, 2) :
      "No server-side QC assessment was returned. Raw epochs are still preserved.";
    return [
      '<section class="panel"><div class="panel-header"><div><div class="panel-title">OID ',
      escapeHtml(oid), ' · filter ', escapeHtml(filterName), '</div>',
      '<div class="panel-subtitle">Field ', escapeHtml(record.fieldid),
      ' · rcid ', escapeHtml(record.rcid), ' · epochs ', epochs.length,
      ' / catalog ', escapeHtml(record.catalog_nepochs),
      ' · payload SHA-256 ', escapeHtml(record.payload_sha256), '</div></div></div>',
      '<div class="panel-subtitle">Time: HMJD · native ZTF magnitude · vertical bars: reported magerr · no cross-OID grouping</div>',
      chart,
      summaryPanel,
      '<div class="panel-title" style="margin-top:18px">Raw epoch records (first 50)</div>',
      '<div class="catalog-table-wrap"><table class="metadata"><thead><tr><th>HMJD</th><th>mag</th>',
      '<th>magerr</th><th>clrcoeff</th><th>catflags</th></tr></thead><tbody>',
      tableRows || '<tr><td colspan="5">No epochs in payload.</td></tr>',
      '</tbody></table></div>',
      '<div class="panel-title" style="margin-top:18px">Raw-preserving QC assessment</div>',
      '<pre class="report-content">', escapeHtml(qcText), '</pre></section>'
    ].join("");
  }

  async function loadRaw() {
    lastRawExport = null;
    desktopDr24Payload = null;
    desktopRawExport = null;
    exportButton.disabled = true;
    let objectids;
    try {
      objectids = parseObjectIds(input.value.trim());
    } catch (error) {
      document.getElementById("dr24Status").textContent = desktopTranslate(error.message);
      return;
    }
    loadButton.disabled = true;
    let activeWorkspace;
    try {
      activeWorkspace = await fetchJson("/v1/workspaces/active");
    } catch (error) {
      document.getElementById("dr24Results").innerHTML =
        '<section class="panel muted">Workspace status is unavailable. No DR24 request was sent.</section>';
      document.getElementById("dr24Provenance").textContent =
        "NOT RUN — active workspace status could not be verified.";
      document.getElementById("dr24Status").textContent =
        "Unable to verify an active workspace. DR24 request was not sent: " +
        (error.message || "workspace service unavailable");
      setConnectionState("Workspace check unavailable", false);
      loadButton.disabled = false;
      return;
    }
    if (!activeWorkspace.workspace) {
      document.getElementById("dr24Results").innerHTML =
        '<section class="panel muted">No acquisition was attempted. Create or open a workspace, then retry the DR24 request.</section>';
      document.getElementById("dr24Provenance").textContent =
        "NOT RUN — no active workspace. No DR24 request was sent.";
      document.getElementById("dr24Status").textContent =
        "Create or open a workspace before requesting DR24 data.";
      setConnectionState("Local API online", true);
      loadButton.disabled = false;
      return;
    }
    let operationId = null;
    try {
      operationId = crypto.randomUUID().replace(/-/g, "");
      await fetchJson("/v1/workspaces/operations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          operation_id: operationId,
          operation_type: "DR24_BATCH_QUERY",
          source: "ztf_dr24_hats",
          status: "RUNNING",
          requested_oids: objectids
        })
      });
      document.getElementById("dr24Status").textContent =
        desktopTranslate("Querying indexed DR24 source for ") + objectids.length +
        desktopTranslate(" OID(s)…");
      const payload = await fetchJson("/v1/dr24/lightcurves", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ objectids })
      });
      const records = Array.isArray(payload.records) ? payload.records : [];
      const qcByOid = new Map((payload.qc_assessments || []).map(item =>
        [String(item.objectid), item]
      ));
      const summaryItems = payload.descriptive_summaries?.summaries || [];
      const summaryByOid = new Map(summaryItems.map(item =>
        [String(item.objectid), item]
      ));
      const provenance = payload.provenance || {};
      await fetchJson("/v1/workspaces/operations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          operation_id: operationId,
          operation_type: "DR24_BATCH_QUERY",
          source: "ztf_dr24_hats",
          status: "SUCCEEDED",
          requested_oids: objectids,
          returned_oids: provenance.returned_oids || [],
          missing_oids: provenance.missing_oids || [],
          payload_sha256_by_oid: provenance.payload_sha256 || {}
        })
      });
      document.getElementById("dr24Provenance").textContent =
        JSON.stringify(provenance, null, 2);
      const rendered = records.map(record =>
        renderRecord(
          record,
          qcByOid.get(String(record.objectid)),
          summaryByOid.get(String(record.objectid))
        )
      );
      document.getElementById("dr24Results").innerHTML = rendered.join("") ||
        '<section class="panel muted">No catalog rows were returned. No alternate source was used.</section>';
      translateDesktopText(document.getElementById("dr24Results"));
      const missing = provenance.missing_oids || [];
      const returned = provenance.returned_oids || records.map(record => record.objectid);
      document.getElementById("dr24Status").textContent =
        "Raw DR24 response received. Requested " + objectids.length +
        " · returned " + returned.length + " · missing " + missing.length +
        ". No feature generation or inference was performed.";
      lastRawExport = {
        export_schema_version: "ztf-dr24-raw-export-v0.3",
        exported_at_utc: new Date().toISOString(),
        source_payload: payload,
        interpretation: "Raw source payload preserved. QC is diagnostic only; no epochs were filtered or grouped."
      };
      desktopDr24Payload = payload;
      desktopRawExport = lastRawExport;
      desktopRawExportPersisted = false;
      translateDesktopText(document.getElementById("dr24Status"));
      exportButton.disabled = false;
      setConnectionState("DR24 raw data loaded");
    } catch (error) {
      if (operationId) {
        try {
          await fetchJson("/v1/workspaces/operations", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              operation_id: operationId,
              operation_type: "DR24_BATCH_QUERY",
              source: "ztf_dr24_hats",
              status: "FAILED",
              requested_oids: objectids,
              returned_oids: [],
              missing_oids: objectids,
              payload_sha256_by_oid: {},
              error_code: "dr24_acquisition_failed",
              error_message: "DR24 acquisition failed. No alternate source was used."
            })
          });
        } catch {
          // Preserve the original acquisition error; the workspace status remains visible.
        }
      }
      document.getElementById("dr24Results").innerHTML =
        '<section class="panel muted">DR24 acquisition failed. No fallback source was used.</section>';
      document.getElementById("dr24Provenance").textContent =
        desktopTranslate("Unavailable: DR24 acquisition failed.");
      desktopDr24Payload = null;
      desktopRawExport = null;
      document.getElementById("dr24Status").textContent =
        error.message || desktopTranslate("DR24 acquisition failed. No fallback source was used.");
      translateDesktopText(document.getElementById("dr24Results"));
      setConnectionState("DR24 acquisition failed", false);
    } finally {
      loadButton.disabled = false;
    }
  }

  loadButton.addEventListener("click", loadRaw);
  exportButton.addEventListener("click", downloadDesktopRawExport);
  if (input.value) await loadRaw();
}
async function showView(view, options = {}) {
  document.querySelectorAll(".nav-item").forEach(item => item.classList.remove("active"));
  const active = document.querySelector('.nav-item[data-view="' + view + '"]');
  if (active) active.classList.add("active");
  if (view === "desktop-home") return renderDesktopHome();
  if (view === "sources") return renderDesktopSources();
  if (view === "workspaces") return renderDesktopWorkspaces();
  if (view === "desktop-provenance") return renderDesktopProvenance();
  if (view === "desktop-export") return renderDesktopExport();
  if (view === "desktop-settings") return renderDesktopSettings();
  if (view === "desktop-help") return renderDesktopHelp();
  if (view === "dr24") return loadDR24Explorer();
  if (view === "overview") {
    mainCanvas.innerHTML = overviewMarkup;
    bindOverviewActions();
    setViewHeading(view);
    const selectedResult = options.result;
    if (selectedResult) {
      state.oid = selectedResult.oid || state.oid;
      state.survey = selectedResult.survey || state.survey;
      renderResult(selectedResult);
      setConnectionState("Saved result loaded", true);
    } else {
      await loadObject();
    }
    return;
  }
  if (view === "catalog") return loadCatalog();
  if (view === "batch") return loadBatchJobs();
  if (view === "reports") return loadReportView();
  if (view === "validation") return loadValidationDashboard();
  if (!state.result && state.oid) await loadObject();
  renderAnalysisModule(view);
}

document.querySelectorAll(".nav-item").forEach(button => {
  button.addEventListener("click", () => showView(button.dataset.view));
});

if (desktopMode) {
  document.title = "ZTF Classifier — Scientific Mission Control";
  document.querySelector(".brand-name").textContent = "ZTF CLASSIFIER";
  document.querySelector(".brand-product").textContent = "Scientific Mission Control";
  document.querySelector(".connection-state").setAttribute("aria-label", "Local service status");
  document.querySelector(".icon-button").setAttribute("aria-label", "Display settings");
  const sectionLabels = document.querySelectorAll(".sidebar .section-label");
  if (sectionLabels[0]) sectionLabels[0].textContent = "MISSION CONTROL";
  if (sectionLabels[1]) sectionLabels[1].hidden = true;
  const desktopViews = new Set([
    "dr24",
    "desktop-home",
    "workspaces",
    "sources",
    "desktop-provenance",
    "desktop-export",
    "desktop-settings",
    "desktop-help",
    "validation",
    "catalog",
    "batch",
  ]);
  const desktopLabels = {
    "desktop-home": "Overview",
    "dr24": "DR24 Explorer",
    "workspaces": "Workspaces",
    "sources": "Data Sources",
    "desktop-provenance": "Provenance",
    "desktop-export": "Reports & Exports",
    "validation": "Scientific Validation",
    "catalog": "Result Catalog",
    "batch": "Analysis Jobs",
    "desktop-settings": "Settings",
    "desktop-help": "Help"
  };
  const desktopSymbols = {
    "desktop-home": "⌂",
    "dr24": "⌁",
    "workspaces": "▣",
    "sources": "◉",
    "desktop-provenance": "◇",
    "desktop-export": "▤",
    "validation": "⚑",
    "catalog": "▦",
    "batch": "◷",
    "desktop-settings": "⚙",
    "desktop-help": "?"
  };
  document.querySelectorAll(".nav-item").forEach(button => {
    button.hidden = !desktopViews.has(button.dataset.view);
    if (desktopLabels[button.dataset.view]) {
      button.textContent = desktopLabels[button.dataset.view];
      const symbol = document.createElement("span");
      symbol.className = "nav-symbol";
      symbol.setAttribute("aria-hidden", "true");
      symbol.textContent = desktopSymbols[button.dataset.view] || "·";
      button.prepend(symbol);
    }
  });
  const desktopNavigationOrder = [
    "desktop-home",
    "dr24",
    "workspaces",
    "catalog",
    "batch",
    "sources",
    "desktop-provenance",
    "validation",
    "desktop-export",
    "desktop-settings",
    "desktop-help",
  ];
  let navigationAnchor = sectionLabels[0];
  for (const view of desktopNavigationOrder) {
    const item = document.querySelector('.nav-item[data-view="' + view + '"]');
    if (item) {
      navigationAnchor.after(item);
      navigationAnchor = item;
    }
  }
  document.querySelectorAll(".desktop-only").forEach(button => { button.hidden = false; });
  document.querySelector(".sidebar-footer").hidden = true;
  document.querySelector(".inspector").hidden = true;
  document.querySelector(".object-actions").hidden = true;
  translateDesktopText(document);
  void showView("desktop-home");
} else {
  bindOverviewActions();
  loadObject();
}
