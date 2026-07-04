(function () {
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/sw.js").catch(function () {});
    });
  }

  var i18n = window.SL_I18N || {};

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve, reject) {
      var textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.setAttribute("readonly", "");
      textarea.style.position = "fixed";
      textarea.style.left = "-9999px";
      document.body.appendChild(textarea);
      textarea.select();
      try {
        var ok = document.execCommand("copy");
        document.body.removeChild(textarea);
        ok ? resolve() : reject(new Error("copy failed"));
      } catch (err) {
        document.body.removeChild(textarea);
        reject(err);
      }
    });
  }

  function showCopied(button, copyLabel, copiedLabel) {
    button.textContent = copiedLabel;
    button.classList.add("copied");
    setTimeout(function () {
      button.textContent = copyLabel;
      button.classList.remove("copied");
    }, 1500);
  }

  var themeBtn = document.getElementById("theme-toggle");
  if (themeBtn) {
    var html = document.documentElement;

    function updateIcon() {
      themeBtn.textContent = html.getAttribute("data-theme") === "dark" ? "☀️" : "🌙";
    }

    updateIcon();
    themeBtn.addEventListener("click", function () {
      var current = html.getAttribute("data-theme");
      var next = current === "dark" ? "light" : "dark";
      html.setAttribute("data-theme", next);
      localStorage.setItem("sl_theme", next);
      updateIcon();
    });
  }

  document.addEventListener("click", function (event) {
    var copyBtn = event.target.closest(".copy-btn");
    if (copyBtn) {
      var text = copyBtn.getAttribute("data-share-url");
      if (!text) {
        var targetId = copyBtn.getAttribute("data-copy-target");
        var input = targetId ? document.getElementById(targetId) : null;
        if (!input) return;
        input.select();
        input.setSelectionRange(0, input.value.length);
        text = input.value;
      }
      var copyLabel = copyBtn.getAttribute("data-copy-label") || i18n.copyBtn || "Copy";
      var copiedLabel = i18n.copiedBtn || "Copied!";
      copyText(text)
        .then(function () {
          showCopied(copyBtn, copyLabel, copiedLabel);
        })
        .catch(function () {
          window.prompt("Copy this link:", text);
        });
      return;
    }

    var openTrigger = event.target.closest("[data-open-dialog]");
    if (openTrigger) {
      var dialog = document.getElementById(openTrigger.getAttribute("data-open-dialog"));
      if (dialog && typeof dialog.showModal === "function") {
        dialog.showModal();
      }
      return;
    }

    var closeTrigger = event.target.closest("[data-close-dialog]");
    if (closeTrigger) {
      var closeDialog = closeTrigger.closest("dialog");
      if (closeDialog) closeDialog.close();
    }
  });

  document.querySelectorAll("dialog").forEach(function (dialog) {
    dialog.addEventListener("click", function (event) {
      if (event.target === dialog) dialog.close();
    });
  });
})();
