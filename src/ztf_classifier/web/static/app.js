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
