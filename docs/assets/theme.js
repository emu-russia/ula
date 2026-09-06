// Light/dark theme toggle for the ULA docs site.
// Theme is picked from localStorage, falling back to the OS preference.
(function () {
  var KEY = "ula-theme";
  var root = document.documentElement;

  function current() {
    var saved = null;
    try { saved = localStorage.getItem(KEY); } catch (e) { /* ignore */ }
    if (saved === "dark" || saved === "light") return saved;
    try {
      if (window.matchMedia &&
          window.matchMedia("(prefers-color-scheme: dark)").matches) {
        return "dark";
      }
    } catch (e) { /* ignore */ }
    return "light";
  }

  function apply(theme) {
    root.setAttribute("data-theme", theme);
  }

  apply(current());

  document.addEventListener("click", function (ev) {
    var btn = ev.target && ev.target.closest
      ? ev.target.closest(".theme-toggle") : null;
    if (!btn) return;
    var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    apply(next);
    try { localStorage.setItem(KEY, next); } catch (e) { /* ignore */ }
  });
})();
