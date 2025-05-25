// extension/popup.js
const toggle = document.getElementById("toggle");
const thresh = document.getElementById("threshold");
const val = document.getElementById("val");

// Load saved settings
chrome.storage.sync.get({ enabled: true, threshold: 0.7 }, prefs => {
  toggle.checked = prefs.enabled;
  thresh.value = prefs.threshold;
  val.innerText = prefs.threshold;
});

// Save on change
toggle.addEventListener("change", () => {
  chrome.storage.sync.set({ enabled: toggle.checked });
  // Your content.js can read this to toggle filtering
});

thresh.addEventListener("input", () => {
  val.innerText = thresh.value;
  chrome.storage.sync.set({ threshold: parseFloat(thresh.value) });
});
