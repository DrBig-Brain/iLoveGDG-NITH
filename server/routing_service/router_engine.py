import json
from typing import Dict, Any, Tuple
from .models_registry import LLM_MODELS_REGISTRY


def select_best_model(prompt: str, prompt_scores: Dict[str, Any]) -> Tuple[Dict[str, Any], str, str]:
    """
    Selects the optimal LLM based on prompt complexity and classification results.
    Returns: (selected_llm_info, category, rationale)
    """
    # Extract scalar metrics safely from list or float
    def get_val(key: str, default: float = 0.0) -> float:
        val = prompt_scores.get(key, default)
        if isinstance(val, (list, tuple)) and len(val) > 0:
            return float(val[0])
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    def get_str(key: str, default: str = "Unknown") -> str:
        val = prompt_scores.get(key, default)
        if isinstance(val, (list, tuple)) and len(val) > 0:
            return str(val[0])
        return str(val)

    complexity = get_val("prompt_complexity_score", 0.10)
    reasoning = get_val("reasoning", 0.05)
    creativity = get_val("creativity_scope", 0.05)
    domain_knowledge = get_val("domain_knowledge", 0.05)
    task_type = get_str("task_type_1", "Question Answering")

    # RULE 1: Simple & Low Complexity Prompts (e.g. "where is Taj mahal located ?")
    # Low complexity threshold (< 0.15) for factual QA, general queries, definitions
    if complexity < 0.15 and task_type in ["Open QA", "Question Answering", "Information Extraction", "Text Summarization", "Unknown"]:
        chosen_key = "gemini-1.5-flash"
        model_info = LLM_MODELS_REGISTRY[chosen_key]
        rationale = (
            f"Prompt complexity score is {complexity:.2f} (Low) with task '{task_type}'. "
            f"Since this is a simple prompt, a lightweight, ultra-fast and cheap LLM "
            f"({model_info['model_id']} at ${model_info['cost_input_per_1m']}/1M input tokens) "
            f"is chosen to minimize latency and operational cost."
        )
        return model_info, "Simple & Cheap", rationale

    # RULE 2: High Reasoning & Deep Logic / Math / Multi-step Deduction / Formal Proofs
    if reasoning >= 0.25 or complexity >= 0.28 or task_type in ["Reasoning", "Problem Solving", "Math"]:
        chosen_key = "o3-mini"
        model_info = LLM_MODELS_REGISTRY[chosen_key]
        rationale = (
            f"Prompt exhibits high complexity ({complexity:.2f}) and reasoning demand ({reasoning:.2f}) "
            f"under task '{task_type}'. Routed to a frontier reasoning model ({model_info['model_id']}) "
            f"equipped with chain-of-thought verification."
        )
        return model_info, "Frontier Reasoning", rationale

    # RULE 3: Code Generation & Technical Software Engineering
    if task_type in ["Code Generation", "Debugging"] or (domain_knowledge >= 0.50 and "code" in prompt.lower()):
        if complexity < 0.22:
            chosen_key = "gpt-4o-mini"
            model_info = LLM_MODELS_REGISTRY[chosen_key]
            rationale = (
                f"Task identified as '{task_type}' with modest complexity ({complexity:.2f}). "
                f"Routed to cost-effective code-capable model ({model_info['model_id']})."
            )
        else:
            chosen_key = "claude-3-5-sonnet"
            model_info = LLM_MODELS_REGISTRY[chosen_key]
            rationale = (
                f"Task identified as '{task_type}' with high complexity ({complexity:.2f}) and domain knowledge ({domain_knowledge:.2f}). "
                f"Routed to premier coding LLM ({model_info['model_id']}) for optimal syntax correctness."
            )
        return model_info, "Code Engineering", rationale

    # RULE 4: Creative Writing / Brainstorming
    if creativity >= 0.35 or task_type in ["Creative Writing", "Brainstorming"]:
        chosen_key = "claude-3-5-sonnet"
        model_info = LLM_MODELS_REGISTRY[chosen_key]
        rationale = (
            f"Creative scope score is high ({creativity:.2f}) for '{task_type}'. "
            f"Routed to high-nuance model ({model_info['model_id']}) for expressive literary output."
        )
        return model_info, "Creative & Nuanced", rationale

    # RULE 5: Default Fallback - Simple or Balanced
    if complexity < 0.15:
        chosen_key = "gemini-1.5-flash"
        model_info = LLM_MODELS_REGISTRY[chosen_key]
        category = "Simple & Cheap"
        rationale = (
            f"Low complexity prompt ({complexity:.2f}). Routed to cheap & fast model {model_info['model_id']}."
        )
    else:
        chosen_key = "gpt-4o"
        model_info = LLM_MODELS_REGISTRY[chosen_key]
        category = "Balanced Production"
        rationale = (
            f"Prompt complexity score is {complexity:.2f} (Moderate) for task '{task_type}'. "
            f"Forwarded to balanced flagship model ({model_info['model_id']}) to ensure quality and speed."
        )
    return model_info, category, rationale


def build_forwarded_query(
    prompt: str,
    model_info: Dict[str, Any],
    client_metadata: Dict[str, Any],
    prompt_scores: Dict[str, Any],
    rationale: str,
    category: str,
) -> Dict[str, Any]:
    """
    Constructs the forwarding payload that shows which LLM the prompt
    was forwarded to, provider endpoint, headers, and simulated response.
    """
    model_id = model_info["model_id"]
    provider = model_info["provider"]
    endpoint = model_info["api_endpoint"]

    # Build provider-specific dispatch query
    if "google" in model_id.lower() or "gemini" in model_id.lower():
        forwarded_payload = {
            "endpoint": endpoint,
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "x-goog-api-key": "[REDACTED_OR_PENDING_USER_KEY]",
            },
            "body": {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 1024,
                },
            },
        }
    elif "anthropic" in model_id.lower() or "claude" in model_id.lower():
        forwarded_payload = {
            "endpoint": endpoint,
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "x-api-key": "[REDACTED_OR_PENDING_USER_KEY]",
                "anthropic-version": "2023-06-01",
            },
            "body": {
                "model": model_id.split("/")[-1],
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1024,
            },
        }
    else:  # OpenAI / DeepSeek format
        forwarded_payload = {
            "endpoint": endpoint,
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer [REDACTED_OR_PENDING_USER_KEY]",
            },
            "body": {
                "model": model_id.split("/")[-1],
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
            },
        }

    # Generate a realistic simulated response since external API keys are pending
    simulated_reply = generate_simulated_reply(prompt, model_info, category)

    return {
        "status": "forwarded",
        "prompt": prompt,
        "routing_decision": {
            "selected_llm": model_id,
            "provider": provider,
            "tier": model_info["tier"],
            "cost_profile": {
                "input_per_million": f"${model_info['cost_input_per_1m']}",
                "output_per_million": f"${model_info['cost_output_per_1m']}",
            },
            "category": category,
            "routing_reason": rationale,
        },
        "classifier_metrics": {
            "task_type": prompt_scores.get("task_type_1", ["Unknown"])[0] if isinstance(prompt_scores.get("task_type_1"), list) else prompt_scores.get("task_type_1"),
            "complexity_score": prompt_scores.get("prompt_complexity_score", [0.0])[0] if isinstance(prompt_scores.get("prompt_complexity_score"), list) else prompt_scores.get("prompt_complexity_score"),
            "reasoning_score": prompt_scores.get("reasoning", [0.0])[0] if isinstance(prompt_scores.get("reasoning"), list) else prompt_scores.get("reasoning"),
            "creativity_score": prompt_scores.get("creativity_scope", [0.0])[0] if isinstance(prompt_scores.get("creativity_scope"), list) else prompt_scores.get("creativity_scope"),
        },
        "authenticated_client": {
            "client_name": client_metadata.get("client_name"),
            "tier": client_metadata.get("tier"),
            "total_requests": client_metadata.get("total_requests"),
        },
        "forwarded_query_payload": forwarded_payload,
        "simulated_llm_response": simulated_reply,
    }


def generate_simulated_reply(prompt: str, model_info: Dict[str, Any], category: str) -> str:
    p_lower = prompt.lower()
    model_name = model_info["model_id"]

    if "taj mahal" in p_lower:
        return (
            f"[{model_name} Response]: The Taj Mahal is located in Agra, Uttar Pradesh, India, "
            f"on the southern bank of the Yamuna River."
        )
    elif "president of india" in p_lower:
        return (
            f"[{model_name} Response]: The President of India is Droupadi Murmu, "
            f"who assumed office on July 25, 2022."
        )
    elif category == "Code Engineering" or "python" in p_lower or "code" in p_lower:
        return (
            f"[{model_name} Code Response]:\n```python\n# Optimized snippet handled by {model_name}\n"
            f"def process_task():\n    return 'Task successfully processed.'\n```"
        )
    elif category == "Frontier Reasoning":
        return (
            f"[{model_name} Chain-of-Thought Response]:\n"
            f"Step 1: Analyzed premise and formal constraints.\n"
            f"Step 2: Applied logical deduction.\n"
            f"Conclusion: Verified result under stated hypotheses."
        )
    else:
        return (
            f"[{model_name} Response]: Successfully routed and processed prompt by {model_info['provider']} "
            f"({model_name})."
        )
