# MULTI-MODEL ROUTER

## About
An intelligent AI middleware gateway between your GenAI application and remote LLM providers. It analyzes incoming prompts, evaluates complexity and task category using an NLP classifier, and automatically routes the prompt to the most cost-effective and capable LLM model.

---

## Architecture & Features

1. **Model Service (`server/model_service`)**:
   - Uses `nvidia/prompt-task-and-complexity-classifier` (DeBERTa-v3 backbone) to predict prompt complexity, task category (Open QA, Code Generation, Reasoning, Creative Writing, etc.), and multi-factor scores (creativity, reasoning, domain knowledge, constraints).
   - Fast fallback heuristic classifier ensures resilient operations offline or during model downloads.
   - Endpoints: `GET /infer?prompt=...` and `POST /infer`.

2. **Auth Service (`server/auth_service`)**:
   - Secure API key generation, validation, usage tracking, and revocation.
   - Persistent SQLite storage (`auth.db`).
   - Default seeded test key: `gdg-test-key-2026`.
   - Endpoints: `POST /auth/keys`, `GET /auth/keys`, `POST /auth/validate`, `POST /auth/revoke`.

3. **Routing Service (`server/routing_service`)**:
   - Intelligent routing engine that evaluates classifier metrics and maps requests to:
     - **Tier 1 (Cheap & Fast)**: `google/gemini-1.5-flash`, `openai/gpt-4o-mini`, `anthropic/claude-3-haiku`
     - **Tier 2 (Balanced / High Capability)**: `openai/gpt-4o`, `anthropic/claude-3-5-sonnet`, `google/gemini-1.5-pro`
     - **Tier 3 (Frontier Reasoning)**: `openai/o3-mini`, `openai/o1`, `deepseek/deepseek-r1`
   - Returns full routing details, rationale, provider dispatch payloads, and simulated responses.
   - Endpoints: `POST /v1/route` and standard OpenAI-compatible `POST /v1/chat/completions`.

4. **Unified Gateway (`server/gateway.py`)**:
   - Mounts Auth, Model, and Routing services in a unified FastAPI gateway with interactive Swagger documentation (`/docs`).

---

## Quick Start

### 1. Run the Gateway Server
```bash
server/model_service/.venv/bin/python server/gateway.py
```
The server will start at `http://localhost:8000`. You can visit `http://localhost:8000/docs` to interact with all endpoints directly.

### 2. Run Tests
```bash
server/model_service/.venv/bin/python server/test_services.py
```

---

## API Examples

### Route a Simple Prompt (e.g. "where is Taj mahal located ?")
```bash
curl -X POST http://localhost:8000/v1/route \
  -H "X-API-Key: gdg-test-key-2026" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "where is Taj mahal located ?"}'
```
**Response:**
```json
{
  "status": "forwarded",
  "prompt": "where is Taj mahal located ?",
  "routing_decision": {
    "selected_llm": "google/gemini-1.5-flash",
    "provider": "Google DeepMind",
    "tier": "Tier 1 (Cheap & Fast)",
    "cost_profile": {
      "input_per_million": "$0.075",
      "output_per_million": "$0.3"
    },
    "category": "Simple & Cheap",
    "routing_reason": "Prompt complexity score is 0.07 (Low) with task 'Open QA'. Since this is a simple prompt, a lightweight, ultra-fast and cheap LLM (google/gemini-1.5-flash at $0.075/1M input tokens) is chosen to minimize latency and operational cost."
  },
  "classifier_metrics": {
    "task_type": "Open QA",
    "complexity_score": 0.06718,
    "reasoning_score": 0.006,
    "creativity_score": 0.0042
  },
  "simulated_llm_response": "[google/gemini-1.5-flash Response]: The Taj Mahal is located in Agra, Uttar Pradesh, India, on the southern bank of the Yamuna River."
}
```

### OpenAI-Compatible Chat Completion
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer gdg-test-key-2026" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "where is Taj mahal located ?"}
    ]
  }'
```

### Generate a New API Key
```bash
curl -X POST http://localhost:8000/auth/keys \
  -H "Content-Type: application/json" \
  -d '{"client_name": "My Client App", "tier": "enterprise"}'
```
