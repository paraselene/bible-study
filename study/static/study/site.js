"use strict";

document.querySelectorAll("[data-auto-submit]").forEach(select => {
  select.addEventListener("change", () => select.form.requestSubmit());
});

// Reload restored private pages so logout/role changes are checked by the server.
window.addEventListener("pageshow", event => {
  if (event.persisted) window.location.reload();
});

const lesson = document.querySelector("[data-lesson]");
if (lesson) {
  const labels = JSON.parse(document.getElementById("study-labels").textContent);
  const prefix = `biblestudy.answers.v1:${lesson.dataset.lesson}:`;
  const inputs = [...document.querySelectorAll("textarea[data-question]")];
  const status = document.getElementById("save-status");
  const showStatus = (message, failed = false) => {
    status.textContent = message;
    status.classList.toggle("error", failed);
  };
  try {
    inputs.forEach(input => { input.value = localStorage.getItem(prefix + input.dataset.question) || ""; });
    // Probe once: disabled storage must not display a misleading saved status.
    localStorage.setItem(prefix + "storage-check", "");
    localStorage.removeItem(prefix + "storage-check");
  } catch {
    showStatus(labels.save_error, true);
  }
  inputs.forEach(input => {
    input.addEventListener("input", () => {
      showStatus(labels.saving);
      try {
        localStorage.setItem(prefix + input.dataset.question, input.value);
        showStatus(labels.saved);
      } catch {
        showStatus(labels.save_error, true);
      }
    });
  });
  const dialog = document.getElementById("clear-dialog");
  document.getElementById("clear-answers").addEventListener("click", () => dialog.showModal());
  dialog.addEventListener("close", () => {
    if (dialog.returnValue !== "clear") return;
    try {
      const keys = Object.keys(localStorage).filter(key => key.startsWith(prefix));
      keys.forEach(key => localStorage.removeItem(key));
      inputs.forEach(input => { input.value = ""; });
      showStatus(labels.cleared);
    } catch {
      showStatus(labels.save_error, true);
    }
  });
}
