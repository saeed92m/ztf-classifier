(() => {
  "use strict";

  const isDesktopPreview =
    new URLSearchParams(window.location.search).get("desktop") === "1";

  if (!isDesktopPreview) {
    return;
  }

  document.documentElement.dataset.desktopPreview = "true";
  document.documentElement.lang = "en";
  document.documentElement.dir = "ltr";

  const pendingErrors = [];
  const report = (message) => {
    const safeMessage = String(message || "Unknown frontend error").slice(0, 2000);
    pendingErrors.push(safeMessage);
    const api = window.pywebview && window.pywebview.api;
    if (api && typeof api.report_frontend_error === "function") {
      Promise.resolve(api.report_frontend_error(safeMessage)).catch(() => {});
    }
  };

  window.addEventListener("error", (event) => {
    const source = event.filename
      ? " (" + event.filename + ":" + (event.lineno || 0) + ")"
      : "";
    report((event.message || "JavaScript error") + source);
  });

  window.addEventListener("unhandledrejection", (event) => {
    const reason = event.reason;
    report(reason && reason.stack ? reason.stack : String(reason));
  });

  window.addEventListener("pywebviewready", () => {
    const api = window.pywebview && window.pywebview.api;
    if (api && typeof api.report_frontend_error === "function") {
      pendingErrors.splice(0).forEach((message) => {
        Promise.resolve(api.report_frontend_error(message)).catch(() => {});
      });
    }
  }, { once: true });
})();
