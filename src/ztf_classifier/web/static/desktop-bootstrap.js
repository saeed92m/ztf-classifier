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
  const frontendErrors = [];
  let bridgeReady = Boolean(window.pywebview && window.pywebview.api);
  let domReady = document.readyState === "interactive" || document.readyState === "complete";

  const sendError = (message) => {
    frontendErrors.push(message);
    const api = window.pywebview && window.pywebview.api;
    if (bridgeReady && api && typeof api.report_frontend_error === "function") {
      Promise.resolve(api.report_frontend_error(message)).catch(() => {});
    } else {
      pendingErrors.push(message);
    }
  };

  const sendStatus = () => {
    if (!bridgeReady || !domReady) return;
    const api = window.pywebview && window.pywebview.api;
    if (!api || typeof api.report_frontend_status !== "function") return;
    const root = document.querySelector("#app");
    const rect = root ? root.getBoundingClientRect() : null;
    const style = root ? window.getComputedStyle(root) : null;
    const status = {
      title: document.title,
      app_root_present: Boolean(root),
      app_root_visible: Boolean(
        root && rect && rect.width > 0 && rect.height > 0 &&
        style && style.display !== "none" && style.visibility !== "hidden"
      ),
      body_text_length: document.body ? document.body.innerText.trim().length : 0,
      frontend_errors: frontendErrors.slice(0, 20)
    };
    Promise.resolve(api.report_frontend_status(status)).catch((error) => {
      sendError("Could not report Workbench DOM status: " + String(error));
    });
  };

  window.addEventListener("error", (event) => {
    const source = event.filename
      ? " (" + event.filename + ":" + (event.lineno || 0) + ")"
      : "";
    sendError((event.message || "JavaScript error") + source);
  });

  window.addEventListener("unhandledrejection", (event) => {
    const reason = event.reason;
    sendError(reason && reason.stack ? reason.stack : String(reason));
  });

  document.addEventListener("DOMContentLoaded", () => {
    domReady = true;
    sendStatus();
  }, { once: true });

  const onBridgeReady = () => {
    bridgeReady = true;
    const api = window.pywebview && window.pywebview.api;
    if (api && typeof api.report_frontend_error === "function") {
      pendingErrors.splice(0).forEach((message) => {
        Promise.resolve(api.report_frontend_error(message)).catch(() => {});
      });
    }
    sendStatus();
  };

  if (bridgeReady) {
    onBridgeReady();
  } else {
    window.addEventListener("pywebviewready", onBridgeReady, { once: true });
  }
})();
