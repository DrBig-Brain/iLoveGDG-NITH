from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class PromptScore(BaseModel):
    task_type_1: List[str]
    task_type_2: List[str]
    task_type_prob: List[float]
    creativity_scope: List[float]
    reasoning: List[float]
    contextual_knowledge: List[float]
    number_of_few_shots: List[float]
    domain_knowledge: List[float]
    no_label_reason: List[float]
    constraint_ct: List[float]
    prompt_complexity_score: List[float]


class ModelInferenceResponse(BaseModel):
    status: int
    prompt: Optional[str] = None
    prompt_scores: Dict[str, Any]


class LLMTarget(BaseModel):
    model_id: str
    provider: str
    tier: str  # "budget", "balanced", "frontier"
    cost_per_million_input: float
    cost_per_million_output: float
    description: str


class RoutingDecision(BaseModel):
    selected_model: str
    provider: str
    tier: str
    task_category: str
    complexity_score: float
    reason: str
    simulated_query_forward: Dict[str, Any]


class ChatCompletionRequest(BaseModel):
    prompt: Optional[str] = None
    messages: Optional[List[Dict[str, str]]] = None
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False


class APIKeyRecord(BaseModel):
    id: int
    api_key: str
    client_name: str
    tier: str
    is_active: bool
    created_at: str
    total_requests: int
