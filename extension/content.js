let buffer = [];
const BATCH_SIZE = 5;
const API_URL = "http://127.0.0.1:8000/check"; // Your FastAPI backend

// Helper: send batch to backend
async function sendBatch() {
  if (!buffer.length) return;
  const texts = buffer.map(item => item.text);
  
  // Check chrome.storage for toggle
  chrome.storage.sync.get({ enabled: true, threshold: 0.7 }, async prefs => {
    if (!prefs.enabled) return;

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: texts.join("\n"), threshold: prefs.threshold })
      });
      const data = await res.json();

      if (data.hateful) {
        buffer.forEach(item => item.node.closest("#comment")?.style?.setProperty("display", "none"));
      }
    } catch (e) {
      console.error("Error checking toxicity:", e);
    }

    buffer = [];
  });
}

// Observe YouTube comments
const observer = new MutationObserver(muts => {
  muts.forEach(m => {
    m.addedNodes.forEach(node => {
      if (node.nodeType === 1) {
        node.querySelectorAll("#content-text").forEach(el => {
          buffer.push({ text: el.innerText, node: el });
          if (buffer.length >= BATCH_SIZE) sendBatch();
        });
      }
    });
  });
});
observer.observe(document.body, { childList: true, subtree: true });

window.addEventListener("beforeunload", () => sendBatch());
