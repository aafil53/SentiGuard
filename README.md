# YouTube Hate‑Speech Blocker

A Chrome Extension + FastAPI ML Backend that detects and blocks toxic or hateful comments in YouTube comment sections in near real time.

## Prerequisites
- Google Chrome or Chromium-based browser
- Python 3.9+ (recommended 3.10/3.11)
- pip

Optional:
- Node not required (no bundler). The extension is plain JS.

## 1) Backend: FastAPI (toxicity classification)

### Setup
1. Create and activate a virtual environment
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies
   ```bash
   pip install -r backend/requirements.txt
   ```
   Note: Installing `torch` may take a while. If you need CPU-only wheels, see PyTorch docs.

3. (Optional) Create a `.env` file in `backend/` to tweak performance and defaults
   ```env
   THRESHOLD=0.7             # default toxicity threshold
   TORCH_NUM_THREADS=1       # limit CPU threads
   SCORE_CACHE_CAPACITY=5000 # LRU cache size for repeated texts
   ```

### Run the server
```bash
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --workers 1
```
The first request will download the `unitary/toxic-bert` model from Hugging Face and cache it locally.

### Verify the API
The `/check` endpoint accepts a JSON body with `texts` (array of strings) and optional `threshold`.
```bash
curl -X POST http://127.0.0.1:8000/check \
  -H 'Content-Type: application/json' \
  -d '{"texts":["You are nice","I hate you"],"threshold":0.7}'
```
Expected response:
```json
{"results":[false,true],"scores":[0.12,0.93]}
```

## 2) Extension: Load into Chrome
1. Build step not needed. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (top-right)
3. Click "Load unpacked" and select the `extension/` folder
4. Ensure the backend is running at `http://127.0.0.1:8000` (default in `content.js`)
5. Open a YouTube video page; the content script will observe and batch-check comments

### Extension controls
- Click the extension icon to open the popup
- Toggle "Enabled" and adjust the "Threshold" slider (saved in `chrome.storage`)

## Notes & Performance
- The content script batches requests, deduplicates processed nodes, and debounces to reduce load
- The backend performs batched inference, dynamic quantization (if available), warmup on startup, and caches scores via an in-memory LRU

## Troubleshooting
- If `torch` fails to install, consult the official install selector for CPU wheels
- First request is slow due to model download; subsequent runs use the local cache
- If you change the backend port or host, update `API_URL` in `extension/content.js`
- If Chrome blocks the extension, ensure only required permissions are present in `extension/manifest.json`

## Optional: YouTube API helper
`backend/youtube_fetcher.py` contains an example of fetching comments with the YouTube Data API. To use it, set `YOUTUBE_API_KEY` in a `.env` and run the script directly.
