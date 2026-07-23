/**
 * ADMIN IMAGE VIEWER — RM Bakes
 * Drop this one script into any admin template and every <img> on
 * the page automatically gets a "Tap to expand" button that opens
 * it full-size in an overlay. No per-page markup needed.
 *
 * Usage: <script src="{{ url_for('static', filename='js/admin-image-viewer.js') }}"></script>
 */
(function () {
  "use strict";

  let modalEls = null;

  function ensureModal() {
    if (modalEls) return modalEls;

    const backdrop = document.createElement("div");
    backdrop.className = "admin-img-modal-backdrop";

    const img = document.createElement("img");
    img.className = "admin-img-modal-img";

    const closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.className = "admin-img-modal-close";
    closeBtn.setAttribute("aria-label", "Close");
    closeBtn.textContent = "×";

    backdrop.appendChild(img);
    backdrop.appendChild(closeBtn);
    document.body.appendChild(backdrop);

    function close() { backdrop.classList.remove("active"); }
    closeBtn.addEventListener("click", close);
    backdrop.addEventListener("click", (e) => { if (e.target === backdrop) close(); });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && backdrop.classList.contains("active")) close();
    });

    modalEls = { backdrop, img };
    return modalEls;
  }

  function openImage(src, alt) {
    const m = ensureModal();
    m.img.src = src;
    m.img.alt = alt || "";
    m.backdrop.classList.add("active");
  }

  function wireUpImage(imgEl) {
    if (imgEl.dataset.zoomWired) return;
    imgEl.dataset.zoomWired = "true";

    const parent = imgEl.parentElement;
    if (!parent) return;

    // Wrap the image so the button can sit on top of it, without
    // touching the image's own sizing/classes/layout.
    const wrap = document.createElement("div");
    wrap.className = "admin-img-zoom-wrap";
    parent.insertBefore(wrap, imgEl);
    wrap.appendChild(imgEl);

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "admin-img-zoom-btn";
    btn.innerHTML = "🔍 Tap to expand";
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      openImage(imgEl.currentSrc || imgEl.src, imgEl.alt);
    });

    wrap.appendChild(btn);
  }

  function scanForImages(root) {
    root.querySelectorAll("img:not([data-zoom-wired])").forEach(wireUpImage);
  }

  document.addEventListener("DOMContentLoaded", () => {
    scanForImages(document);

    // Catch images added later (e.g. live previews when editing a
    // product/carousel/coupon banner) without needing every admin
    // page to call anything manually.
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((m) => {
        m.addedNodes.forEach((node) => {
          if (node.nodeType !== 1) return;
          if (node.tagName === "IMG") wireUpImage(node);
          else if (node.querySelectorAll) scanForImages(node);
        });
      });
    });
    observer.observe(document.body, { childList: true, subtree: true });
  });
})();
