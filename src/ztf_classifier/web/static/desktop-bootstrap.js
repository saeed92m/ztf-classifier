(() => {
  "use strict";

  const isDesktopPreview =
    new URLSearchParams(window.location.search).get("desktop") === "1";

  if (!isDesktopPreview) {
    return;
  }

  document.documentElement.dataset.desktopPreview = "true";
  document.documentElement.lang = "fa";
  document.documentElement.dir = "rtl";
})();
