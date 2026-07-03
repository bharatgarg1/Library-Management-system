document.addEventListener("DOMContentLoaded", () => {

  const sidebar     = document.getElementById("sidebar");
  const mainContent = document.getElementById("mainContent");
  const toggleBtn   = document.getElementById("sidebarToggle");

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", () => {
      if (window.innerWidth <= 768) {
        sidebar.classList.toggle("mobile-open");
      } else {
        sidebar.classList.toggle("collapsed");
        mainContent?.classList.toggle("expanded");
      }
    });
  }

  const htmlEl    = document.documentElement;
  const themeBtn  = document.getElementById("themeToggle");
  const themeIcon = document.getElementById("themeIcon");
  const saved     = localStorage.getItem("lms-theme") || "light";
  applyTheme(saved);

  themeBtn?.addEventListener("click", () => {
    const next = htmlEl.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
    applyTheme(next);
    localStorage.setItem("lms-theme", next);
  });

  function applyTheme(theme) {
    htmlEl.setAttribute("data-bs-theme", theme);
    if (themeIcon) {
      themeIcon.className = theme === "dark" ? "bi bi-sun-fill" : "bi bi-moon-stars-fill";
    }
  }

  document.querySelectorAll(".alert.fade.show").forEach(el => {
    setTimeout(() => bootstrap.Alert.getOrCreateInstance(el)?.close(), 4000);
  });

});