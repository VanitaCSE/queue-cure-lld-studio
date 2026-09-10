document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".alert").forEach((alert) => {
    window.setTimeout(() => alert.remove(), 5000);
  });
});