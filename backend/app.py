# backend/app.py

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# You can adjust the threshold here or make it dynamic later
THRESHOLD = 0.7

app = FastAPI()

# Allow cross‑origin calls (for local testing). Lock this down in production!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the tokenizer and model once at startup
tokenizer = AutoTokenizer.from_pretrained("unitary/toxic-bert")
model = AutoModelForSequenceClassification.from_pretrained("unitary/toxic-bert")
model.eval()  # turn off dropout, etc.

# Pydantic model for incoming JSON
class TextIn(BaseModel):
    text: str

@app.post("/check")
def check_text(payload: TextIn):
    """
    Accepts JSON {"text": <string>}
    Returns {"hateful": <bool>, "score": <float>}
    """
    try:
        # Tokenize and get logits
        inputs = tokenizer(payload.text, return_tensors="pt", truncation=True)
        with torch.no_grad():
            logits = model(**inputs).logits

        # Convert logits to probabilities
        scores = torch.softmax(logits, dim=1)[0]
        toxic_score = float(scores[1])  # index 1 is "toxic"

        return {
            "hateful": toxic_score >= THRESHOLD,
            "score": toxic_score
        }
    except Exception as e:
        # In case of errors, return a 500 with the exception message
        raise HTTPException(status_code=500, detail=str(e))
