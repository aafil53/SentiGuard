# YouTube Hate‑Speech Blocker

Chrome extension + FastAPI backend that classifies YouTube comments for toxicity and hides those above a threshold.

## Quickstart
1) Backend (FastAPI)
- Create venv and install deps
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```
- Start API
```bash
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --workers 1
```

2) Extension (Chrome)
- Go to `chrome://extensions/` → enable Developer mode
- Click "Load unpacked" → select the `extension/` folder
- Open a YouTube video page; the extension will batch‑check comments

## Verify
- API: send a test request
```bash
curl -s -X POST http://127.0.0.1:8000/check \
  -H 'Content-Type: application/json' \
  -d '{"texts":["You are kind","I hate you"],"threshold":0.7}' | jq
```
- Extension: click the icon → toggle Enabled and adjust Threshold. Hateful comments should hide automatically when loaded.

## Configuration
Create `backend/.env` (optional) to tune defaults:
```env
THRESHOLD=0.7             # default toxicity threshold
TORCH_NUM_THREADS=1       # CPU thread limit for PyTorch
SCORE_CACHE_CAPACITY=5000 # in‑memory LRU cache size
```
If you run the API on a non‑default host/port, update `API_URL` in `extension/content.js`.

## What’s inside
- `backend/app.py`: FastAPI app using `unitary/toxic-bert`
  - Batched inference, startup warmup
  - Dynamic quantization (if available) for faster CPU and smaller model
  - In‑memory LRU cache to skip recomputation for repeated texts
- `extension/`
  - `content.js`: MutationObserver → debounced, chunked requests; per‑item filtering; pref cache
  - `manifest.json`: minimal permissions; `document_idle` load
  - `popup.html`, `popup.js`, `style.css`: enable/threshold controls

## Performance tips
- First run downloads the model (one‑time cold start). Subsequent runs use the cache.
- Keep `TORCH_NUM_THREADS=1` (or small) on small CPUs to avoid contention.
- For heavier traffic, consider:
  - Smaller model or distilled variant on HF
  - ONNX Runtime / BetterTransformer for speedups
  - Running the API near the client to reduce latency

## Troubleshooting
- PyTorch install slow/fails: consult official selector for CPU‑only wheels.
- 404/connection errors from the extension: ensure the API is running and `API_URL` matches.
- Comments not hiding: verify popup "Enabled" is on and threshold isn’t too high.

## License
MIT (or your preferred license).
