# backend/app.py

import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from collections import OrderedDict

# Load environment variables from .env
load_dotenv()

# You can adjust the threshold here or make it dynamic later
THRESHOLD = float(os.getenv("THRESHOLD", 0.7))

# Optionally limit PyTorch intraop threads to reduce CPU contention in small servers
try:
    torch.set_num_threads(int(os.getenv("TORCH_NUM_THREADS", "1")))
except Exception:
    pass

app = FastAPI()

# Allow cross‑origin calls (for local testing). Lock this down in production!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the tokenizer and model once at startup
_tokenizer = AutoTokenizer.from_pretrained("unitary/toxic-bert")
_model = AutoModelForSequenceClassification.from_pretrained("unitary/toxic-bert")

# Dynamic quantization on Linear layers can reduce model size and speed up CPU inference
try:
    _model = torch.quantization.quantize_dynamic(_model, {torch.nn.Linear}, dtype=torch.qint8)
except Exception:
    # If quantization is not available, continue with the original model
    pass

_model.eval()  # turn off dropout, etc.


class TextsIn(BaseModel):
    texts: List[str]
    threshold: Optional[float] = None


class _ScoreCache:
    def __init__(self, capacity: int = 5000) -> None:
        self.capacity = capacity
        self.store: OrderedDict[str, float] = OrderedDict()

    def get(self, key: str) -> Optional[float]:
        if key in self.store:
            self.store.move_to_end(key)
            return self.store[key]
        return None

    def set(self, key: str, value: float) -> None:
        if key in self.store:
            self.store.move_to_end(key)
        self.store[key] = value
        if len(self.store) > self.capacity:
            self.store.popitem(last=False)


_score_cache = _ScoreCache(capacity=int(os.getenv("SCORE_CACHE_CAPACITY", "5000")))


@app.on_event("startup")
def warm_model() -> None:
    """Run a tiny forward pass to trigger any lazy init and reduce first-request latency."""
    try:
        with torch.no_grad():
            inputs = _tokenizer([""], return_tensors="pt", truncation=True, padding=True)
            _ = _model(**inputs).logits
    except Exception:
        # Warmup failures should not prevent the app from starting
        pass


@app.post("/check")
def check_texts(payload: TextsIn):
    """
    Accepts JSON {"texts": [str], "threshold": float?}
    Returns {"results": [bool], "scores": [float]}
    """
    try:
        if not payload.texts:
            return {"results": [], "scores": []}

        # Split into cached and uncached
        cached_scores: List[Optional[float]] = []
        to_infer_texts: List[str] = []
        to_infer_indices: List[int] = []
        for idx, text in enumerate(payload.texts):
            cached = _score_cache.get(text)
            cached_scores.append(cached)
            if cached is None:
                to_infer_texts.append(text)
                to_infer_indices.append(idx)

        # Batch infer only for cache misses
        if to_infer_texts:
            inputs = _tokenizer(to_infer_texts, return_tensors="pt", truncation=True, padding=True)
            with torch.no_grad():
                logits = _model(**inputs).logits
            scores_tensor = torch.softmax(logits, dim=1)[:, 1]
            inferred_scores: List[float] = [float(s) for s in scores_tensor]

            # Write back to cache and place into results
            for local_idx, score in enumerate(inferred_scores):
                global_idx = to_infer_indices[local_idx]
                cached_scores[global_idx] = score
                _score_cache.set(payload.texts[global_idx], score)

        # All scores are now filled
        scores: List[float] = [float(s) for s in cached_scores]  # type: ignore
        threshold = payload.threshold if payload.threshold is not None else THRESHOLD
        results: List[bool] = [s >= threshold for s in scores]

        return {"results": results, "scores": scores}
    except Exception as e:
        # In case of errors, return a 500 with the exception message
        raise HTTPException(status_code=500, detail=str(e))
