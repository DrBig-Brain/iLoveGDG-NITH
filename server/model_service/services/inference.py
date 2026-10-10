import os
import json
import logging
from typing import Dict, Any, Optional

try:
    from services.fallback_classifier import heuristic_classify_prompt
except ImportError:
    try:
        from .fallback_classifier import heuristic_classify_prompt
    except ImportError:
        from server.model_service.services.fallback_classifier import heuristic_classify_prompt

logger = logging.getLogger(__name__)


def inference(model, tokenizer, prompt: str) -> Dict[str, Any]:
    if not prompt or not isinstance(prompt, str):
        prompt = ""

    if model is not None and tokenizer is not None:
        try:
            model.eval()
            encoded_prompt = tokenizer(
                prompt,
                return_tensors="pt",
                add_special_tokens=True,
                max_length=512,
                padding="max_length",
                truncation=True,
            )
            result = model(encoded_prompt)
            return result
        except Exception as e:
            logger.warning(f"PyTorch model inference failed with: {e}. Falling back to heuristic classifier.")

    # Fallback to heuristic classifier
    return heuristic_classify_prompt(prompt)


if __name__ == "__main__":
    from services.load_model import load_model
    m, t = load_model()
    prompt = "Who is the president of India ?"
    res = inference(m, t, prompt)
    print("Inference result:", res)
