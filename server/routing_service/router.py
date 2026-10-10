import os
import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from server.auth_service.router import verify_api_key_header
from .router_engine import select_best_model, build_forwarded_query

logger = logging.getLogger("routing_service")
router = APIRouter(prefix="/v1", tags=["Routing Middleware"])

MODEL_SERVICE_URL = os.environ.get("MODEL_SERVICE_URL", "http://localhost:8000")


class RoutePromptRequest(BaseModel):
    prompt: str = Field(..., description="The user prompt to analyze and forward to the appropriate LLM")
    max_tokens: Optional[int] = Field(1024, description="Optional maximum tokens for generation")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature")


class ChatCompletionMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    messages: List[ChatCompletionMessage]
    model: Optional[str] = "auto"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1024


async def get_prompt_scores(prompt: str) -> Dict[str, Any]:
    """
    Fetches complexity and classification scores from model-service.
    Tries direct in-memory inference first; if not loaded, calls HTTP endpoint.
    """
    # 1. Try direct in-memory call from model_service if available
    try:
        from server.model_service.main import run_inference
        scores = run_inference(prompt)
        if scores:
            return scores
    except Exception as in_mem_err:
        logger.debug(f"In-memory model service inference skipped: {in_mem_err}")

    # 2. Try HTTP call to model_service
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{MODEL_SERVICE_URL}/infer", json={"prompt": prompt})
            if resp.status_code == 200:
                data = resp.json()
                return data.get("prompt_scores", {})
    except Exception as http_err:
        logger.warning(f"HTTP call to model service failed ({http_err}). Using heuristic fallback.")

    # 3. Direct heuristic fallback
    from server.model_service.services.fallback_classifier import heuristic_classify_prompt
    return heuristic_classify_prompt(prompt)


@router.post("/route")
async def route_prompt(
    req: RoutePromptRequest,
    client: Dict[str, Any] = Depends(verify_api_key_header),
):
    """
    Main middleware endpoint:
    1. Authenticates client using API key.
    2. Classifies prompt complexity & task using model-service.
    3. Runs routing logic to choose optimal LLM.
    4. Returns which LLM was selected, why it was chosen, and the forwarded payload.
    """
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    # Get classification results from model-service
    prompt_scores = await get_prompt_scores(prompt)

    # Run routing decision engine
    model_info, category, rationale = select_best_model(prompt, prompt_scores)

    # Build the forwarding query response
    response_data = build_forwarded_query(
        prompt=prompt,
        model_info=model_info,
        client_metadata=client,
        prompt_scores=prompt_scores,
        rationale=rationale,
        category=category,
    )

    return response_data


@router.post("/chat/completions")
async def openai_compatible_completions(
    req: ChatCompletionRequest,
    client: Dict[str, Any] = Depends(verify_api_key_header),
):
    """
    OpenAI-compatible chat completions endpoint that acts as intelligent middleware router.
    Extracts the latest user message, determines the best LLM, and dispatches.
    """
    if not req.messages:
        raise HTTPException(status_code=400, detail="Messages list cannot be empty")

    # Find the latest user message
    user_prompt = ""
    for msg in reversed(req.messages):
        if msg.role.lower() == "user":
            user_prompt = msg.content
            break

    if not user_prompt:
        user_prompt = req.messages[-1].content

    prompt_scores = await get_prompt_scores(user_prompt)
    model_info, category, rationale = select_best_model(user_prompt, prompt_scores)

    result = build_forwarded_query(
        prompt=user_prompt,
        model_info=model_info,
        client_metadata=client,
        prompt_scores=prompt_scores,
        rationale=rationale,
        category=category,
    )

    # Return standard OpenAI-compatible response structure with routing metadata
    return {
        "id": f"chatcmpl-{os.urandom(8).hex()}",
        "object": "chat.completion",
        "model": model_info["model_id"],
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": result["simulated_llm_response"],
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": len(user_prompt.split()),
            "completion_tokens": len(result["simulated_llm_response"].split()),
            "total_tokens": len(user_prompt.split()) + len(result["simulated_llm_response"].split()),
        },
        "middleware_metadata": {
            "routing_decision": result["routing_decision"],
            "classifier_metrics": result["classifier_metrics"],
            "forwarded_query_payload": result["forwarded_query_payload"],
        },
    }
