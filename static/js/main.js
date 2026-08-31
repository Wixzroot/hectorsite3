// Close the mobile nav after a link inside it is clicked.
document.addEventListener('DOMContentLoaded', function () {
  var toggle = document.getElementById('nav-toggle');
  var nav = document.querySelector('.site-nav');
  if (!toggle || !nav) return;

  nav.querySelectorAll('a').forEach(function (link) {
    link.addEventListener('click', function () {
      toggle.checked = false;
    });
  });
});
