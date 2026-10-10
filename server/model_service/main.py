from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional
from fastapi.responses import JSONResponse
import logging

try:
    from services.load_model import load_model
    from services.inference import inference
except ImportError:
    from .services.load_model import load_model
    from .services.inference import inference

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("model_service")

app = FastAPI(
    title="Model Service",
    description="NLP Prompt Complexity & Task Classifier",
    version="1.0.0",
)

model, tokenizer = load_model()


class InferRequest(BaseModel):
    prompt: str


def run_inference(prompt: str):
    return inference(model, tokenizer, prompt)


@app.get("/")
def root():
    return {
        "name": "Model-service",
        "status": "running",
        "model_loaded": model is not None,
    }


@app.get("/infer")
def infer_get(prompt: str = Query(..., description="Prompt to evaluate")):
    try:
        results = run_inference(prompt)
        return {
            "status": 200,
            "prompt": prompt,
            "prompt_scores": results,
        }
    except Exception as e:
        logger.error(f"Inference error: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": 500, "message": str(e)},
        )


@app.post("/infer")
def infer_post(req: InferRequest):
    try:
        results = run_inference(req.prompt)
        return {
            "status": 200,
            "prompt": req.prompt,
            "prompt_scores": results,
        }
    except Exception as e:
        logger.error(f"Inference error: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": 500, "message": str(e)},
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
