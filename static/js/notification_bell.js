document.addEventListener('DOMContentLoaded', function () {
  const bellBtn = document.getElementById('notifBellBtn');
  const popup = document.getElementById('notifPopup');

  if (!bellBtn || !popup) return;

  bellBtn.addEventListener('click', function (e) {
    e.stopPropagation();
    popup.classList.toggle('open');
  });

  document.addEventListener('click', function (e) {
    if (!popup.contains(e.target) && !bellBtn.contains(e.target)) {
      popup.classList.remove('open');
    }
  });
});