/* Small progressive-enhancement behaviours. */
document.addEventListener("DOMContentLoaded", function () {
  // Auto-dismiss toasts after 6s.
  document.querySelectorAll(".toast").forEach(function (t) {
    setTimeout(function () {
      t.style.transition = "opacity .4s";
      t.style.opacity = "0";
      setTimeout(function () { t.remove(); }, 450);
    }, 6000);
  });
  document.querySelectorAll(".toast-close").forEach(function (b) {
    b.addEventListener("click", function () { b.closest(".toast").remove(); });
  });

  // Mobile sidebar toggle.
  var toggle = document.getElementById("sidebarToggle");
  if (toggle) {
    toggle.addEventListener("click", function () {
      document.body.classList.toggle("sidebar-open");
    });
    document.querySelector(".content").addEventListener("click", function () {
      document.body.classList.remove("sidebar-open");
    });
  }
});
