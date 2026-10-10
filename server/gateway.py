import os
import sys

# Ensure repository root and server dir are in PYTHONPATH
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import sub-service routers
from server.auth_service.router import router as auth_router
from server.routing_service.router import router as routing_router
from server.model_service.main import app as model_app

app = FastAPI(
    title="Multi-Model Router Gateway",
    description=(
        "Middleware connecting GenAI applications and LLM providers. "
        "Evaluates prompt complexity, classifies tasks, enforces API key authentication, "
        "and automatically routes prompts to the most cost-effective and capable LLMs."
    ),
    version="1.0.0",
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Auth and Routing routers
app.include_router(auth_router)
app.include_router(routing_router)

# Mount Model Service routes directly on the gateway as well
@app.get("/infer", tags=["Model Service"])
def model_infer_get(prompt: str):
    from server.model_service.main import infer_get
    return infer_get(prompt=prompt)


@app.post("/infer", tags=["Model Service"])
def model_infer_post(req: dict):
    from server.model_service.main import infer_post, InferRequest
    return infer_post(InferRequest(prompt=req.get("prompt", "")))


@app.get("/api", tags=["General"])
def gateway_api_info():
    return {
        "service": "Multi-Model Router Gateway",
        "status": "online",
        "default_test_api_key": "gdg-test-key-2026",
        "endpoints": {
            "auth": {
                "create_key": "POST /auth/keys",
                "list_keys": "GET /auth/keys",
                "validate_key": "POST /auth/validate",
                "revoke_key": "POST /auth/revoke",
            },
            "model_service": {
                "infer_get": "GET /infer?prompt=...",
                "infer_post": "POST /infer",
            },
            "routing_middleware": {
                "route_prompt": "POST /v1/route",
                "chat_completions": "POST /v1/chat/completions",
            },
            "docs": "/docs",
            "ui": "/",
        },
    }


@app.get("/health", tags=["General"])
def health_check():
    return {"status": "healthy"}


# Mount client static frontend
CLIENT_DIR = os.path.join(PROJECT_ROOT, "client")
if os.path.isdir(CLIENT_DIR):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=CLIENT_DIR, html=True), name="client")


if __name__ == "__main__":
    uvicorn.run(
        "gateway:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
