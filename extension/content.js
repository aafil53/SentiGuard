let buffer = [];
const API_URL = "http://127.0.0.1:8000/check"; // FastAPI backend

// Track processed comment nodes to avoid duplicates
const processed = new WeakSet();

// Cached prefs to avoid frequent storage reads
let prefsCache = { enabled: true, threshold: 0.7 };
chrome.storage.sync.get(prefsCache, (prefs) => {
  prefsCache = prefs;
});
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === "sync") {
    if (changes.enabled) prefsCache.enabled = changes.enabled.newValue;
    if (changes.threshold) prefsCache.threshold = changes.threshold.newValue;
  }
});

// Debounce helper
function debounce(fn, delay) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), delay);
  };
}

async function postBatch(items) {
  const texts = items.map((item) => item.text);
  const res = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ texts, threshold: prefsCache.threshold }),
    keepalive: true,
  });
  return res.json();
}

async function flush() {
  if (!buffer.length) return;
  if (!prefsCache.enabled) {
    buffer = [];
    return;
  }

  // Chunk to avoid very large payloads
  const CHUNK_SIZE = 50;
  try {
    for (let i = 0; i < buffer.length; i += CHUNK_SIZE) {
      const chunk = buffer.slice(i, i + CHUNK_SIZE);
      // eslint-disable-next-line no-await-in-loop
      const data = await postBatch(chunk);
      const { results } = data || {};
      if (Array.isArray(results)) {
        results.forEach((isHateful, idx) => {
          if (isHateful) {
            chunk[idx].node.closest("#comment")?.style?.setProperty("display", "none");
          }
        });
      }
    }
  } catch (e) {
    console.error("Error checking toxicity:", e);
  }

  buffer = [];
}

const debouncedFlush = debounce(flush, 250);

// Observe YouTube comments efficiently
const observer = new MutationObserver((muts) => {
  let added = 0;
  for (const m of muts) {
    m.addedNodes.forEach((node) => {
      if (node.nodeType === 1) {
        node.querySelectorAll("#content-text").forEach((el) => {
          if (processed.has(el)) return;
          processed.add(el);
          buffer.push({ text: el.textContent || "", node: el });
          added += 1;
        });
      }
    });
  }
  if (added) debouncedFlush();
});
observer.observe(document.body, { childList: true, subtree: true });

window.addEventListener("beforeunload", () => flush());
