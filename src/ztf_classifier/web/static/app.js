const STORAGE_KEY = "ztf-workbench-appearance";

const defaults = {
  theme: "auto",
  dayStart: "06:00",
  nightStart: "18:00",
};

function loadPreferences() {
  try {
    return { ...defaults, ...JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}") };
  } catch {
    return { ...defaults };
  }
}

function timeToMinutes(value) {
  const [hours, minutes] = value.split(":").map(Number);
  return hours * 60 + minutes;
}

function resolveTheme(preferences) {
  if (preferences.theme === "deep-space" || preferences.theme === "alpha" || preferences.theme === "light") {
    return preferences.theme;
  }
  if (preferences.theme === "system") {
    return "system";
  }
  const now = new Date();
  const minutes = now.getHours() * 60 + now.getMinutes();
  const day = timeToMinutes(preferences.dayStart);
  const night = timeToMinutes(preferences.nightStart);
  const isDay = day < night
    ? minutes >= day && minutes < night
    : minutes >= day || minutes < night;
  return isDay ? "light" : "alpha";
}

function applyTheme(preferences) {
  document.documentElement.dataset.theme = resolveTheme(preferences);
}

function savePreferences(preferences) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
  applyTheme(preferences);
}

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

themeButton.addEventListener("click", () => {
  popover.hidden = !popover.hidden;
});

themeSelect.addEventListener("change", () => {
  preferences.theme = themeSelect.value;
  savePreferences(preferences);
});
dayStart.addEventListener("change", () => {
  preferences.dayStart = dayStart.value;
  savePreferences(preferences);
});
nightStart.addEventListener("change", () => {
  preferences.nightStart = nightStart.value;
  savePreferences(preferences);
});

setInterval(() => {
  if (preferences.theme === "auto") applyTheme(preferences);
}, 60_000);

document.querySelectorAll(".nav-item").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".nav-item").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    document.getElementById("viewTitle").textContent = button.textContent;
    document.getElementById("viewSubtitle").textContent =
      button.dataset.view === "overview"
        ? "Scientific overview · 150-sample benchmark workspace"
        : "Workbench module · API-backed scientific analysis surface";
  });
});


async function loadLightCurve() {
  const params = new URLSearchParams(window.location.search);
  const oid = params.get("oid") || document.getElementById("viewTitle").textContent.trim();
  const svg = document.getElementById("lightCurveSvg");
  if (!svg || !oid) return;

  try {
    const response = await fetch(
      `/v1/objects/${encodeURIComponent(oid)}/observations?survey=ztf`,
      { headers: { Accept: "application/json" } },
    );
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    renderLightCurve(svg, payload.observations || []);
  } catch (error) {
    svg.setAttribute("aria-label", "Light curve unavailable");
    svg.insertAdjacentHTML(
      "beforeend",
      '<text x="450" y="140" text-anchor="middle" class="chart-message">Observation data unavailable</text>',
    );
  }
}

function renderLightCurve(svg, observations) {
  svg.querySelectorAll(".dynamic-light-curve").forEach((node) => node.remove());
  if (!observations.length) return;

  const xValues = observations.map((item) => Number(item.mjd));
  const yValues = observations.map((item) => Number(item.mag));
  const xMin = Math.min(...xValues);
  const xMax = Math.max(...xValues);
  const yMin = Math.min(...yValues);
  const yMax = Math.max(...yValues);
  const xSpan = Math.max(xMax - xMin, 1e-9);
  const ySpan = Math.max(yMax - yMin, 1e-9);

  const plot = observations
    .map((item) => {
      const x = ((Number(item.mjd) - xMin) / xSpan) * 900;
      const y = 240 - ((Number(item.mag) - yMin) / ySpan) * 200;
      return { x, y };
    })
    .sort((a, b) => a.x - b.x);

  const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
  group.setAttribute("class", "dynamic-light-curve");

  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("class", "curve-line");
  path.setAttribute("d", plot.map((point, index) =>
    `${index === 0 ? "M" : "L"}${point.x.toFixed(2)} ${point.y.toFixed(2)}`
  ).join(" "));
  group.appendChild(path);

  const points = document.createElementNS("http://www.w3.org/2000/svg", "g");
  points.setAttribute("class", "points");
  plot.forEach((point) => {
    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", point.x.toFixed(2));
    circle.setAttribute("cy", point.y.toFixed(2));
    circle.setAttribute("r", "3");
    points.appendChild(circle);
  });
  group.appendChild(points);
  svg.appendChild(group);
}

loadLightCurve();
