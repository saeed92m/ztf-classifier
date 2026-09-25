
const STORAGE_KEY = "ztf-workbench-appearance";
const defaults = { theme: "auto", dayStart: "06:00", nightStart: "18:00" };
const params = new URLSearchParams(window.location.search);
const state = {
  oid: params.get("oid") || "",
  survey: params.get("survey") || "ztf",
  observations: [],
  result: null,
};

function loadPreferences() {
  try { return { ...defaults, ...JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}") }; }
  catch { return { ...defaults }; }
}
function timeToMinutes(value) {
  const parts = value.split(":").map(Number);
  return parts[0] * 60 + parts[1];
}
function resolveTheme(p) {
  if (["deep-space", "alpha", "light"].includes(p.theme)) return p.theme;
  if (p.theme === "system") return "system";
  const minutes = new Date().getHours() * 60 + new Date().getMinutes();
  const day = timeToMinutes(p.dayStart), night = timeToMinutes(p.nightStart);
  const isDay = day < night ? minutes >= day && minutes < night : minutes >= day || minutes < night;
  return isDay ? "light" : "alpha";
}
function applyTheme(p) { document.documentElement.dataset.theme = resolveTheme(p); }
function savePreferences(p) { localStorage.setItem(STORAGE_KEY, JSON.stringify(p)); applyTheme(p); }

const preferences = loadPreferences();
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
themeSelect.addEventListener("change", () => { preferences.theme = themeSelect.value; savePreferences(preferences); });
dayStart.addEventListener("change", () => { preferences.dayStart = dayStart.value; savePreferences(preferences); });
nightStart.addEventListener("change", () => { preferences.nightStart = nightStart.value; savePreferences(preferences); });
setInterval(() => { if (preferences.theme === "auto") applyTheme(preferences); }, 60000);

function setConnectionState(label, ok) {
  const node = document.querySelector(".connection-state");
  if (!node) return;
  node.innerHTML = '<span class="status-dot"></span>' + label;
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
async function fetchJson(url, options) {
  const response = await fetch(url, {
    headers: { Accept: "application/json", ...((options && options.headers) || {}) },
    ...(options || {}),
  });
  if (!response.ok) { const error = new Error("HTTP " + response.status); error.status = response.status; throw error; }
  return response.json();
}
function clearPrediction() {
  document.getElementById("predictedClass").textContent = "—";
  document.getElementById("topProbability").textContent = "—";
  document.getElementById("conformalSet").textContent = "—";
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
const titles = {
  overview: ["Object analysis", "Scientific overview"],
  observations: ["Observations", "Normalized observation stream"],
  features: ["Features", "Scientific Feature Engine output"],
  classification: ["Classification", "Model prediction and probabilities"],
  uncertainty: ["Uncertainty & OOD", "Conformal and anomaly diagnostics"],
  provenance: ["Provenance", "Traceable scientific metadata"],
  batch: ["Batch jobs", "Durable analysis jobs"],
  catalog: ["Catalog", "Catalog query and export module"],
  reports: ["Reports", "Scientific report generation module"],
};
document.querySelectorAll(".nav-item").forEach(button => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".nav-item").forEach(item => item.classList.remove("active"));
    button.classList.add("active");
    const view = button.dataset.view;
    document.getElementById("viewTitle").textContent = view === "overview" ? state.oid : titles[view][0];
    document.getElementById("viewSubtitle").textContent = titles[view][1];
    if (view === "overview") loadObject();
  });
});
document.getElementById("runAnalysisButton").addEventListener("click", runAnalysis);
document.getElementById("exportReportButton").addEventListener("click", async () => {
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
});
loadObject();
