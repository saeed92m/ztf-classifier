
const STORAGE_KEY = "ztf-workbench-appearance";
const defaults = { theme: "auto", dayStart: "06:00", nightStart: "18:00" };
const params = new URLSearchParams(window.location.search);
const desktopMode = params.get("desktop") === "1";
let desktopDr24Payload = null;
let desktopRawExport = null;
const desktopTranslations = {
  "ALPHA": "ZTF CLASSIFIER",
  "Scientific Analysis Workbench": "نسخه آزمایشی دسکتاپ",
  "API ready": "اتصال محلی برقرار است",
  "Open theme settings": "تنظیمات نمایش",
  "ANALYSIS": "کاوش داده",
  "Overview": "نمای کلی",
  "Observations": "رصدها",
  "DR24 Explorer (raw)": "کاوش داده‌های خام DR24",
  "Features": "ویژگی‌ها",
  "Classification": "طبقه‌بندی",
  "Uncertainty & OOD": "عدم‌قطعیت و OOD",
  "Provenance": "منشأ داده",
  "WORKSPACE": "فضای کار",
  "Batch jobs": "پردازش دسته‌ای",
  "Catalog": "کاتالوگ",
  "Reports": "گزارش‌ها",
  "Scientific Validation": "اعتبارسنجی علمی",
  "MODEL": "مدل",
  "API": "رابط محلی",
  "v1 · API-backed": "نسخه آزمایشی · API محلی",
  "OBJECT ANALYSIS": "تحلیل جرم",
  "Select an object": "شناسه جرم را وارد کنید",
  "Provide an object ID to load scientific data": "برای دریافت داده، شناسه DR24 را وارد کنید",
  "Export report": "خروجی گزارش",
  "Run analysis": "اجرای تحلیل",
  "Predicted class": "کلاس پیش‌بینی‌شده",
  "Top probability": "بیشترین احتمال",
  "Conformal set": "مجموعه همدیس",
  "OOD percentile": "صدک OOD",
  "Light curve": "منحنی نوری",
  "Observation-domain view · flux/magnitude history": "نمای داده رصدی · تاریخچه شار/قدر",
  "observations": "رصدها",
  "uncertainty": "عدم‌قطعیت",
  "mag": "قدر",
  "Calibrated probability distribution": "توزیع احتمال کالیبره",
  "Details": "جزئیات",
  "Scientific context": "زمینه علمی",
  "Traceable analysis metadata": "فراداده تحلیل قابل ردیابی",
  "Object ID": "شناسه جرم",
  "Feature schema": "طرح‌واره ویژگی",
  "Model": "مدل",
  "Calibration": "کالیبراسیون",
  "Data provenance": "منشأ داده",
  "OBJECT INSPECTOR": "بازرس جرم",
  "ZTF OBJECT": "جرم ZTF",
  "Coordinates from loaded observation metadata": "مختصات از فراداده رصد دریافت‌شده",
  "ANALYSIS STATE": "وضعیت تحلیل",
  "Inference": "استنتاج",
  "Conformal": "همدیس",
  "Dataset": "مجموعه‌داده",
  "Model artifact": "آرتیفکت مدل",
  "Schema": "طرح‌واره",
  "Open provenance graph": "نمایش گراف منشأ",
  "Appearance": "ظاهر",
  "Theme": "پوسته",
  "Auto": "خودکار",
  "System": "سیستم",
  "Deep Space": "فضای ژرف",
  "Alpha Theme": "پوسته Alpha",
  "Light": "روشن",
  "Day starts": "شروع روز",
  "Night starts": "شروع شب",
  "Auto follows local clock; System follows the operating-system preference.": "حالت خودکار از ساعت محلی پیروی می‌کند؛ حالت سیستم از تنظیمات Windows.",
  "SOURCE EXPLORER · EXPERIMENTAL": "کاوشگر منبع · آزمایشی",
  "DR24 Explorer": "کاوشگر DR24",
  "Native DR24 data only. No feature normalization or model inference.": "فقط داده خام DR24. هیچ نرمال‌سازی ویژگی یا استنتاج مدلی انجام نمی‌شود.",
  "Indexed multi-OID lookup": "جست‌وجوی شاخص‌محور چندشناسه‌ای",
  "Enter 1–10 positive ZTF DR24 object IDs. Separate OIDs remain separate records; no broad catalog scan is performed.": "۱ تا ۱۰ شناسه مثبت ZTF DR24 وارد کنید. هر OID یک رکورد مستقل است؛ اسکن گسترده کاتالوگ انجام نمی‌شود.",
  "DR24 object IDs": "شناسه‌های جرم DR24",
  "One or more OIDs, separated by commas or spaces": "یک یا چند OID؛ با ویرگول یا فاصله جدا کنید",
  "Load raw light curves": "دریافت منحنی‌های نوری خام",
  "Download raw JSON + QC": "دریافت JSON خام + QC",
  "No DR24 objects loaded.": "هنوز داده‌ای از DR24 دریافت نشده است.",
  "Enter up to 10 OIDs to inspect native DR24 records.": "برای مشاهده داده خام، حداکثر ۱۰ OID وارد کنید.",
  "Acquisition provenance": "منشأ دریافت داده",
  "Source, schema, query, missing OIDs and payload hashes": "منبع، طرح‌واره، پرس‌وجو، OIDهای مفقود و هش داده",
  "No acquisition performed.": "هنوز دریافت داده انجام نشده است.",
  "Raw epoch records (first 50)": "ردیف‌های خام زمانی (۵۰ مورد نخست)",
  "Raw-preserving QC assessment": "ارزیابی QC با حفظ داده خام",
  "No epochs in payload.": "در این داده ردیف زمانی وجود ندارد.",
  "No server-side QC assessment was returned. Raw epochs are still preserved.": "ارزیابی QC از سرور دریافت نشد. ردیف‌های خام حفظ شده‌اند.",
  "No DR24 export available": "خروجی DR24 در دسترس نیست",
  "DR24 acquisition failed": "دریافت DR24 ناموفق بود",
  "Local settings unavailable": "تنظیمات محلی در دسترس نیست",
  "Object required": "شناسه جرم لازم است",
  "Descriptive time-series summary": "خلاصه توصیفی سری زمانی",
  "Source-native descriptive statistics · not model features or classification": "آمار توصیفی مستقیم از منبع · نه ویژگی مدل و نه طبقه‌بندی",
  "Finite HMJD/mag pairs": "زوج‌های معتبر HMJD/قدر",
  "HMJD span (days)": "بازه HMJD (روز)",
  "Median sampling interval (days)": "میانه فاصله نمونه‌برداری (روز)",
  "Median magnitude": "میانه قدر",
  "Magnitude P05–P95 range": "بازه قدر P05–P95",
  "Median non-negative magerr": "میانه خطای قدر غیرمنفی",
  "All finite HMJD/magnitude pairs are included, regardless of catflags. No epoch filtering, time conversion, photometry conversion, OID grouping, feature generation, or inference was performed.": "تمام زوج‌های معتبر HMJD/قدر، بدون توجه به catflags، در آمار آمده‌اند. هیچ ردیف زمانی حذف نشده و تبدیل زمان، تبدیل نورسنجی، گروه‌بندی OID، تولید ویژگی یا استنتاج انجام نشده است.",
  "Time: HMJD · native ZTF magnitude · vertical bars: reported magerr · no cross-OID grouping": "زمان: HMJD · قدر خام ZTF · میله‌های عمودی: magerr گزارش‌شده · بدون گروه‌بندی بین OIDها",
  "Field": "میدان",
  "filter": "فیلتر",
  "rcid": "rcid",
  "epochs": "ردیف‌های زمانی",
  "catalog": "کاتالوگ",
  "payload SHA-256": "هش SHA-256 داده",
  "No finite numeric HMJD/magnitude pairs are available to plot. Raw rows remain available below and in the JSON export.": "زوج عددی معتبر HMJD/قدر برای نمودار وجود ندارد. ردیف‌های خام در جدول و خروجی JSON حفظ شده‌اند.",
  "HMJD": "HMJD",
  "magerr": "magerr",
  "clrcoeff": "clrcoeff",
  "catflags": "catflags",
  "Diagnostic QC": "کنترل کیفیت تشخیصی",
  "DIAGNOSTIC_NOT_PRODUCTION_APPROVED": "تشخیصی · تأییدنشده برای تولید",
  "DR24 raw data loaded": "داده خام DR24 دریافت شد",
  "No catalog rows were returned. No alternate source was used.": "هیچ ردیفی از کاتالوگ بازنگشت. منبع جایگزین استفاده نشد.",
  "DR24 acquisition failed. No fallback source was used.": "دریافت DR24 ناموفق بود. منبع جایگزین استفاده نشد.",
  "Unavailable: DR24 acquisition failed.": "در دسترس نیست: دریافت DR24 ناموفق بود."
};
function desktopTranslate(value) {
  if (!desktopMode || typeof value !== "string") return value;
  let translated = desktopTranslations[value] || value;
  const replacements = [
    ["Querying indexed DR24 source for ", "در حال پرس‌وجوی منبع شاخص‌گذاری‌شده DR24 برای "],
    [" OID(s)…", " OID…"],
    ["Raw DR24 response received. Requested ", "پاسخ خام DR24 دریافت شد. درخواست‌شده: "],
    [" · returned ", " · دریافت‌شده: "],
    [" · missing ", " · مفقود: "],
    [". No feature generation or inference was performed.", ". هیچ ویژگی یا استنتاجی تولید نشد."],
    ["DR24 acquisition failed (", "دریافت DR24 ناموفق بود ("],
    ["). No fallback source was used.", "). منبع جایگزین استفاده نشد."],
    ["Enter between 1 and 10 object IDs.", "بین ۱ تا ۱۰ شناسه وارد کنید."],
    ["Every object ID must be a positive integer.", "هر شناسه باید عدد صحیح مثبت باشد."],
    ["Every object ID must be a safe positive integer.", "هر شناسه باید عدد صحیح مثبت و قابل‌نمایش باشد."],
    ["Duplicate object IDs are not allowed.", "OID تکراری مجاز نیست."],
    [" · filter ", " · فیلتر "],
    ["Field ", "میدان "],
    [" · epochs ", " · ردیف زمانی "],
    [" / catalog ", " / کاتالوگ "],
    [" · payload SHA-256 ", " · هش SHA-256 داده "],
    ["Time: HMJD", "زمان: HMJD"],
    ["native ZTF magnitude", "قدر خام ZTF"],
    ["vertical bars: reported magerr", "میله‌های عمودی: magerr گزارش‌شده"],
    ["no cross-OID grouping", "بدون گروه‌بندی بین OIDها"]
  ];
  for (const [source, target] of replacements) {
    translated = translated.replaceAll(source, target);
  }
  return translated;
}
function translateDesktopText(root = document) {
  if (!desktopMode || !root) return;
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  for (const node of nodes) {
    const original = node.nodeValue || "";
    const trimmed = original.trim();
    if (!trimmed) continue;
    const translated = desktopTranslate(trimmed);
    if (translated !== trimmed) node.nodeValue = original.replace(trimmed, translated);
  }
  if (root.querySelectorAll) {
    root.querySelectorAll("[placeholder], [aria-label]").forEach(element => {
      if (element.hasAttribute("placeholder")) {
        element.setAttribute("placeholder", desktopTranslate(element.getAttribute("placeholder")));
      }
      if (element.hasAttribute("aria-label")) {
        element.setAttribute("aria-label", desktopTranslate(element.getAttribute("aria-label")));
      }
    });
  }
}
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
  if (p.theme === "system") return "system";
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
    desktopTokenPromise = new Promise((resolve, reject) => {
      const readToken = () => {
        const getter = window.pywebview && window.pywebview.api &&
          window.pywebview.api.get_api_token;
        if (typeof getter !== "function") {
          reject(new Error("Desktop authentication bridge is unavailable."));
          return;
        }
        Promise.resolve(getter()).then(resolve, reject);
      };
      if (window.pywebview && window.pywebview.api) {
        readToken();
        return;
      }
      const timeout = window.setTimeout(
        () => reject(new Error("Desktop authentication bridge did not become ready.")),
        10000
      );
      window.addEventListener("pywebviewready", () => {
        window.clearTimeout(timeout);
        readToken();
      }, { once: true });
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
  uncertainty: ["Uncertainty / OOD / Anomaly", "Independent diagnostic channels"],
  provenance: ["Provenance", "Traceable scientific metadata"],
  batch: ["Batch jobs", "Durable analysis jobs"],
  catalog: ["Catalog", "Catalog query and export module"],
  reports: ["Reports", "Scientific report generation module"],
  validation: ["Scientific Validation", "Release-blocking scientific evidence and provenance"],
  "desktop-home": ["داشبورد", "نمای کلی نسخه آزمایشی پارک"],
  sources: ["منبع داده", "منبع فعال و قرارداد دریافت داده"],
  "desktop-provenance": ["منشأ داده", "فراداده و شواهد دریافت"],
  "desktop-export": ["گزارش و خروجی", "خروجی خام JSON و اطلاعات بازتولید"],
  "desktop-settings": ["تنظیمات", "تنظیمات محلی برنامه"],
  "desktop-help": ["راهنما", "راهنمای استفاده و محدوده علمی نسخه"],
};

function renderDesktopHome() {
  mainCanvas.innerHTML = `
    <div class="canvas-header"><div><div class="eyebrow">نسخه آزمایشی پارک فناوری</div>
    <h1 id="viewTitle"></h1><p id="viewSubtitle"></p></div></div>
    <section class="metric-grid">
      <article class="metric-card"><span>منبع داده</span><strong>ZTF DR24</strong><small>IRSA HATS · دریافت زنده</small></article>
      <article class="metric-card"><span>حالت پردازش</span><strong>RAW + DESCRIPTIVE</strong><small>داده خام، QC تشخیصی و آمار توصیفی</small></article>
      <article class="metric-card"><span>مدل طبقه‌بندی</span><strong>NOT RUN</strong><small>در این نسخه فعال نیست</small></article>
      <article class="metric-card"><span>خروجی</span><strong>JSON + Provenance</strong><small>پس از دریافت موفق داده</small></article>
    </section>
    <section class="panel">
      <div class="panel-title">شروع کار</div>
      <p class="muted">یک تا ده شناسه ZTF DR24 وارد کنید. برنامه داده خام را از منبع اصلی دریافت می‌کند و منحنی نوری، QC تشخیصی، آمار توصیفی و منشأ داده را نمایش می‌دهد.</p>
      <button class="primary-button" id="startDr24Explorer" type="button">شروع کاوش داده DR24</button>
    </section>
    <section class="panel">
      <div class="panel-title">محدوده علمی این نسخه</div>
      <p>این نسخه داده خام و آمار توصیفی را نمایش می‌دهد. طبقه‌بندی، احتمال کالیبره، Abstention، OOD و کشف ناهنجاری در این نسخه اجرا نمی‌شوند.</p>
      <p class="muted">اگر دریافت داده ناقص یا ناموفق باشد، وضعیت واقعی نمایش داده می‌شود. برنامه از منبع جایگزین استفاده نمی‌کند.</p>
    </section>`;
  setViewHeading("desktop-home");
  document.getElementById("startDr24Explorer").addEventListener("click", () => showView("dr24"));
}

function renderDesktopSources() {
  mainCanvas.innerHTML = `
    <div class="canvas-header"><div><div class="eyebrow">DATA SOURCE</div><h1 id="viewTitle"></h1><p id="viewSubtitle"></p></div></div>
    <section class="panel">
      <div class="panel-title">IRSA ZTF DR24 Lightcurves HATS</div>
      <div class="panel-subtitle">منبع فعال نسخه آزمایشی</div>
      <dl class="metadata">
        <div><dt>انتشار</dt><dd>DR24</dd></div>
        <div><dt>شاخص جست‌وجو</dt><dd>objectid</dd></div>
        <div><dt>فیلترها</dt><dd>g / r / i</dd></div>
        <div><dt>حد درخواست</dt><dd>۱ تا ۱۰ OID</dd></div>
        <div><dt>نیاز شبکه</dt><dd>اتصال اینترنت لازم است</dd></div>
        <div><dt>منبع جایگزین</dt><dd>استفاده نمی‌شود</dd></div>
      </dl>
    </section>
    <section class="panel">
      <div class="panel-title">قرارداد داده</div>
      <ul>
        <li>زمان خام با ستون HMJD حفظ می‌شود؛ HMJD با MJD یکسان نیست.</li>
        <li>قدر و خطای قدر خام ZTF حفظ می‌شوند.</li>
        <li>catflags بدون ماسک‌کردن یا حذف ردیف‌ها نگهداری می‌شود.</li>
        <li>هر OID یک رکورد مستقل است؛ گروه‌بندی منبع فیزیکی انجام نمی‌شود.</li>
      </ul>
    </section>`;
  setViewHeading("sources");
}

function renderDesktopProvenance() {
  const provenance = desktopDr24Payload?.provenance;
  mainCanvas.innerHTML = `
    <div class="canvas-header"><div><div class="eyebrow">PROVENANCE</div><h1 id="viewTitle"></h1><p id="viewSubtitle"></p></div></div>
    <section class="panel">
      <div class="panel-title">وضعیت منشأ داده</div>
      <p class="muted">${provenance ? "داده از منبع DR24 دریافت شده است." : "NOT RUN · هنوز دریافت داده‌ای انجام نشده است."}</p>
      <pre class="report-content" id="desktopProvenanceJson">${provenance ? escapeHtml(JSON.stringify(provenance, null, 2)) : "NOT RUN"}</pre>
    </section>`;
  setViewHeading("desktop-provenance");
}

function downloadDesktopRawExport() {
  if (!desktopRawExport) {
    setConnectionState("No DR24 export available", false);
    return;
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
}

function renderDesktopExport() {
  const available = Boolean(desktopRawExport);
  const provenance = desktopDr24Payload?.provenance || {};
  mainCanvas.innerHTML = `
    <div class="canvas-header"><div><div class="eyebrow">EXPORT</div><h1 id="viewTitle"></h1><p id="viewSubtitle"></p></div></div>
    <section class="panel">
      <div class="panel-title">خروجی خام JSON</div>
      <p class="muted">${available ? "آماده دریافت" : "NOT RUN · ابتدا داده DR24 را دریافت کنید."}</p>
      <dl class="metadata">
        <div><dt>طرح‌واره خروجی</dt><dd>${available ? "ztf-dr24-raw-export-v0.3" : "—"}</dd></div>
        <div><dt>OIDهای درخواست‌شده</dt><dd>${escapeHtml((provenance.requested_oids || []).join(", ") || "—")}</dd></div>
        <div><dt>OIDهای دریافت‌شده</dt><dd>${escapeHtml((provenance.returned_oids || []).join(", ") || "—")}</dd></div>
        <div><dt>OIDهای مفقود</dt><dd>${escapeHtml((provenance.missing_oids || []).join(", ") || "—")}</dd></div>
      </dl>
      <button class="primary-button" id="desktopDownloadJson" type="button" ${available ? "" : "disabled"}>دریافت فایل JSON</button>
    </section>`;
  setViewHeading("desktop-export");
  const button = document.getElementById("desktopDownloadJson");
  button.addEventListener("click", downloadDesktopRawExport);
}

async function renderDesktopSettings() {
  mainCanvas.innerHTML = `
    <div class="canvas-header"><div><div class="eyebrow">SETTINGS</div><h1 id="viewTitle"></h1><p id="viewSubtitle"></p></div></div>
    <section class="panel">
      <div class="panel-title">تنظیمات نمایش</div>
      <p>برای تغییر پوسته، از دکمه تنظیمات در نوار بالای برنامه استفاده کنید.</p>
      <p class="muted">تنظیمات و فایل‌های کاری در فضای کاربری Windows ذخیره می‌شوند. حذف برنامه، داده‌های کاربر را حذف نمی‌کند.</p>
    </section>
    <section class="panel">
      <div class="panel-title">وضعیت اتصال</div>
      <p id="desktopSettingsStatus" class="muted">در حال بررسی سرویس محلی…</p>
    </section>`;
  setViewHeading("desktop-settings");
  const status = document.getElementById("desktopSettingsStatus");
  try {
    await fetchJson("/v1/settings");
    status.textContent = "سرویس محلی در دسترس است.";
  } catch {
    status.textContent = "سرویس محلی در دسترس نیست.";
  }
}

function renderDesktopHelp() {
  mainCanvas.innerHTML = `
    <div class="canvas-header"><div><div class="eyebrow">HELP & ABOUT</div><h1 id="viewTitle"></h1><p id="viewSubtitle"></p></div></div>
    <section class="panel">
      <div class="panel-title">راهنمای سریع</div>
      <ol>
        <li>به بخش «کاوش DR24» بروید.</li>
        <li>یک تا ده OID مثبت وارد کنید.</li>
        <li>دریافت داده را اجرا کنید و وضعیت درخواست را بررسی کنید.</li>
        <li>منحنی نوری، جدول ردیف‌های خام، QC و آمار توصیفی را بررسی کنید.</li>
        <li>منشأ داده را بازبینی و فایل JSON را دریافت کنید.</li>
      </ol>
    </section>
    <section class="panel">
      <div class="panel-title">محدودیت‌ها</div>
      <ul>
        <li>دریافت زنده به اتصال اینترنت نیاز دارد.</li>
        <li>QC این نسخه تشخیصی است و تأیید تولیدی ندارد.</li>
        <li>آمار توصیفی، ویژگی مدل نیست.</li>
        <li>طبقه‌بندی و کشف ناهنجاری در این نسخه اجرا نمی‌شوند.</li>
        <li>OID شناسه کاتالوگی است و به‌تنهایی هویت یک منبع فیزیکی را ثابت نمی‌کند.</li>
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
    desktopMode ? '<button class="secondary-button" id="dr24SampleButton" type="button">شناسه‌های نمونه آزمون‌شده</button><small class="muted">این دو OID نمونه، دو رکورد مستقل‌اند.</small>' : '',
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
    document.getElementById("dr24Status").textContent =
      desktopTranslate("Querying indexed DR24 source for ") + objectids.length +
      desktopTranslate(" OID(s)…");
    try {
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
      translateDesktopText(document.getElementById("dr24Status"));
      exportButton.disabled = false;
      setConnectionState("DR24 raw data loaded");
    } catch (error) {
      document.getElementById("dr24Results").innerHTML =
        '<section class="panel muted">DR24 acquisition failed. No fallback source was used.</section>';
      document.getElementById("dr24Provenance").textContent =
        desktopTranslate("Unavailable: DR24 acquisition failed.");
      desktopDr24Payload = null;
      desktopRawExport = null;
      document.getElementById("dr24Status").textContent =
        desktopTranslate("DR24 acquisition failed (") + (error.status || "network") +
        desktopTranslate("). No fallback source was used.");
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
async function showView(view) {
  document.querySelectorAll(".nav-item").forEach(item => item.classList.remove("active"));
  const active = document.querySelector('.nav-item[data-view="' + view + '"]');
  if (active) active.classList.add("active");
  if (view === "desktop-home") return renderDesktopHome();
  if (view === "sources") return renderDesktopSources();
  if (view === "desktop-provenance") return renderDesktopProvenance();
  if (view === "desktop-export") return renderDesktopExport();
  if (view === "desktop-settings") return renderDesktopSettings();
  if (view === "desktop-help") return renderDesktopHelp();
  if (view === "dr24") return loadDR24Explorer();
  if (view === "overview") {
    mainCanvas.innerHTML = overviewMarkup;
    bindOverviewActions();
    setViewHeading(view);
    await loadObject();
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
  document.title = "ZTF Classifier | نسخه آزمایشی پارک";
  document.querySelector(".brand-name").textContent = "ZTF CLASSIFIER";
  document.querySelector(".brand-product").textContent = "نسخه آزمایشی دسکتاپ";
  document.querySelector(".connection-state").setAttribute("aria-label", "وضعیت سرویس محلی");
  document.querySelector(".icon-button").setAttribute("aria-label", "تنظیمات نمایش");
  const sectionLabels = document.querySelectorAll(".sidebar .section-label");
  if (sectionLabels[0]) sectionLabels[0].textContent = "فضای کار";
  if (sectionLabels[1]) sectionLabels[1].hidden = true;
  const desktopViews = new Set([
    "dr24",
    "desktop-home",
    "sources",
    "desktop-provenance",
    "desktop-export",
    "desktop-settings",
    "desktop-help",
  ]);
  document.querySelectorAll(".nav-item").forEach(button => {
    button.hidden = !desktopViews.has(button.dataset.view);
  });
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
