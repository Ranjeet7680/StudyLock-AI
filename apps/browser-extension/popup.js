document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.getElementById("toggleBtn");
  const statusBadge = document.getElementById("statusBadge");
  const timerDisplay = document.getElementById("timerDisplay");
  const timerSubtext = document.getElementById("timerSubtext");

  let countdownInterval = null;
  let remainingSeconds = 25 * 60;

  function updateUI(isActive) {
    if (isActive) {
      statusBadge.textContent = "ENFORCING";
      statusBadge.className = "badge badge-active";
      toggleBtn.textContent = "End Focus Session (Exit)";
      toggleBtn.className = "btn btn-stop";
      timerSubtext.textContent = "Restrictions Active";
      startTimer();
    } else {
      statusBadge.textContent = "IDLE";
      statusBadge.className = "badge badge-inactive";
      toggleBtn.textContent = "Start Focus Session";
      toggleBtn.className = "btn btn-primary";
      timerSubtext.textContent = "Ready to Focus";
      stopTimer();
      timerDisplay.textContent = "25:00";
    }
  }

  function startTimer() {
    if (countdownInterval) clearInterval(countdownInterval);
    countdownInterval = setInterval(() => {
      if (remainingSeconds > 0) {
        remainingSeconds--;
        const mins = String(Math.floor(remainingSeconds / 60)).padStart(2, '0');
        const secs = String(remainingSeconds % 60).padStart(2, '0');
        timerDisplay.textContent = `${mins}:${secs}`;
      } else {
        clearInterval(countdownInterval);
        updateUI(false);
      }
    }, 1000);
  }

  function stopTimer() {
    if (countdownInterval) clearInterval(countdownInterval);
    remainingSeconds = 25 * 60;
  }

  // Load existing state
  chrome.storage.local.get(["isFocusActive"], (data) => {
    updateUI(Boolean(data.isFocusActive));
  });

  // Toggle button handler
  toggleBtn.addEventListener("click", () => {
    chrome.runtime.sendMessage({ type: "TOGGLE_FOCUS" }, (response) => {
      if (response && response.status === "success") {
        updateUI(response.isFocusActive);
      }
    });
  });
});
