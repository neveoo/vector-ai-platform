"""
Document classification.

Two paths, on purpose (this is the Phase 3 piece from our planning
discussion -- it's what separates "called an LLM API" from "trained
and evaluated a model"):

1. classify_with_trained_model: a small fine-tuned classifier
   (embedding + logistic regression head, or a distilled transformer)
   trained on a labeled set of document examples. TODO: train this in
   a notebook under /notebooks, export with joblib, load it here.
2. classify_with_llm_prompt: fallback for document classes the trained
   model hasn't seen, or before a trained model exists at all.

Recording `classification_method` on the Document row (see
app/models/document.py) makes it easy to demo both paths and compare
their accuracy/latency/cost in the eval writeup.
"""
import json
from pathlib import Path

from app.core.config import get_settings

settings = get_settings()

TRAINED_MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "document_classifier.joblib"

CANDIDATE_CLASSES = ["contract", "invoice", "policy", "report", "correspondence", "other"]


def classify_document(text: str) -> tuple[str, float, str]:
    """Returns (predicted_class, confidence, method)."""
    if TRAINED_MODEL_PATH.exists():
        return _classify_with_trained_model(text)
    return _classify_with_llm_prompt(text)


def _classify_with_trained_model(text: str) -> tuple[str, float, str]:
    import joblib

    from app.services.embeddings import embed_texts

    pipeline = joblib.load(TRAINED_MODEL_PATH)
    vector = embed_texts([text])
    predicted = pipeline.predict(vector)[0]
    confidence = float(max(pipeline.predict_proba(vector)[0]))
    return predicted, confidence, "trained_model"


def _classify_with_llm_prompt(text: str) -> tuple[str, float, str]:
    from anthropic import Anthropic

    client = Anthropic(api_key=settings.anthropic_api_key)
    prompt = (
        "Classify the following document into exactly one of these categories: "
        f"{', '.join(CANDIDATE_CLASSES)}.\n\n"
        "Respond with only a JSON object: {\"class\": \"...\", \"confidence\": 0.0-1.0}\n\n"
        f"Document text (truncated):\n{text[:4000]}"
    )
    response = client.messages.create(
        model=settings.chat_model,
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}],
    )
    result = json.loads(response.content[0].text)
    return result["class"], float(result["confidence"]), "llm_prompt"
