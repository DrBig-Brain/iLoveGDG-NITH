import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from server.gateway import app

client = TestClient(app)


def test_auth_workflow():
    print("\n--- Testing Authentication Service ---")

    # 1. Test unauthenticated request is blocked
    unauth_resp = client.post("/v1/route", json={"prompt": "where is Taj mahal located ?"})
    assert unauth_resp.status_code == 401, f"Expected 401, got {unauth_resp.status_code}"
    print("  [PASS] Blocked unauthenticated request (401)")

    # 2. Test default seeded demo key
    headers = {"X-API-Key": "gdg-test-key-2026"}
    auth_resp = client.post(
        "/v1/route",
        headers=headers,
        json={"prompt": "where is Taj mahal located ?"},
    )
    assert auth_resp.status_code == 200, f"Expected 200 with default key, got {auth_resp.status_code}: {auth_resp.text}"
    print("  [PASS] Authenticated successfully with default demo key 'gdg-test-key-2026'")

    # 3. Test generate new API key
    gen_resp = client.post(
        "/auth/keys",
        json={"client_name": "My Custom App", "tier": "enterprise"},
    )
    assert gen_resp.status_code == 200
    new_key = gen_resp.json()["key_data"]["api_key"]
    print(f"  [PASS] Generated new API key: {new_key}")

    # 4. Test request with newly generated API key using Bearer header
    bearer_headers = {"Authorization": f"Bearer {new_key}"}
    resp_with_new_key = client.post(
        "/v1/route",
        headers=bearer_headers,
        json={"prompt": "What is the capital of France?"},
    )
    assert resp_with_new_key.status_code == 200
    print("  [PASS] Authenticated with newly created key via Bearer token")

    # 5. Revoke key
    revoke_resp = client.post("/auth/revoke", json={"api_key": new_key})
    assert revoke_resp.status_code == 200
    print(f"  [PASS] Revoked API key: {new_key}")

    # 6. Verify revoked key is now rejected
    blocked_resp = client.post(
        "/v1/route",
        headers=bearer_headers,
        json={"prompt": "Hello"},
    )
    assert blocked_resp.status_code == 401
    print("  [PASS] Revoked API key correctly rejected (401)")


def test_model_inference():
    print("\n--- Testing Model Inference Service ---")

    # Test GET /infer
    res = client.get("/infer", params={"prompt": "where is Taj mahal located ?"})
    assert res.status_code == 200
    data = res.json()
    scores = data["prompt_scores"]
    print(f"  [PASS] Prompt: 'where is Taj mahal located ?'")
    print(f"         Complexity Score: {scores['prompt_complexity_score'][0]}")
    print(f"         Task Type 1: {scores['task_type_1'][0]}")


def test_routing_scenarios():
    print("\n--- Testing Routing Logic Scenarios ---")
    headers = {"X-API-Key": "gdg-test-key-2026"}

    # SCENARIO 1: Simple Prompt ("where is Taj mahal located ?")
    simple_prompt = "where is Taj mahal located ?"
    res_simple = client.post(
        "/v1/route",
        headers=headers,
        json={"prompt": simple_prompt},
    )
    assert res_simple.status_code == 200
    body_simple = res_simple.json()
    decision_simple = body_simple["routing_decision"]
    print(f"\n[Test 1 - Simple Prompt]: '{simple_prompt}'")
    print(f"  -> Metrics:      {body_simple['classifier_metrics']}")
    print(f"  -> Selected LLM: {decision_simple['selected_llm']}")
    print(f"  -> Provider:     {decision_simple['provider']}")
    print(f"  -> Tier:         {decision_simple['tier']}")
    print(f"  -> Reason:       {decision_simple['routing_reason']}")
    print(f"  -> Simulated:    {body_simple['simulated_llm_response']}")
    assert "Cheap & Fast" in decision_simple["tier"], f"Expected cheap/fast tier, got {decision_simple['tier']}"

    # SCENARIO 2: Code Generation Prompt
    code_prompt = "Write a Python script that implements binary search on a sorted list."
    res_code = client.post(
        "/v1/route",
        headers=headers,
        json={"prompt": code_prompt},
    )
    assert res_code.status_code == 200
    body_code = res_code.json()
    decision_code = body_code["routing_decision"]
    print(f"\n[Test 2 - Code Prompt]: '{code_prompt}'")
    print(f"  -> Metrics:      {body_code['classifier_metrics']}")
    print(f"  -> Selected LLM: {decision_code['selected_llm']}")
    print(f"  -> Tier:         {decision_code['tier']}")
    print(f"  -> Reason:       {decision_code['routing_reason']}")

    # SCENARIO 3: Complex Multi-step Logic / Math Reasoning Prompt
    reasoning_prompt = (
        "Prove that every planar graph is 4-colorable and provide formal topological lemmas "
        "with step-by-step mathematical deduction."
    )
    res_math = client.post(
        "/v1/route",
        headers=headers,
        json={"prompt": reasoning_prompt},
    )
    assert res_math.status_code == 200
    body_math = res_math.json()
    decision_math = body_math["routing_decision"]
    print(f"\n[Test 3 - Reasoning Prompt]: '{reasoning_prompt}'")
    print(f"  -> Metrics:      {body_math['classifier_metrics']}")
    print(f"  -> Selected LLM: {decision_math['selected_llm']}")
    print(f"  -> Tier:         {decision_math['tier']}")
    print(f"  -> Reason:       {decision_math['routing_reason']}")


def test_openai_compatible_endpoint():
    print("\n--- Testing OpenAI-Compatible /v1/chat/completions ---")
    headers = {"Authorization": "Bearer gdg-test-key-2026"}
    res = client.post(
        "/v1/chat/completions",
        headers=headers,
        json={
            "messages": [
                {"role": "user", "content": "where is Taj mahal located ?"}
            ]
        },
    )
    assert res.status_code == 200
    data = res.json()
    print(f"  [PASS] Endpoint responded in OpenAI schema format:")
    print(f"         Model Chosen: {data['model']}")
    print(f"         Message Content: {data['choices'][0]['message']['content']}")
    print(f"         Selected Provider: {data['middleware_metadata']['routing_decision']['provider']}")


def test_ui_endpoints():
    print("\n--- Testing UI Endpoints ---")
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "Multi-Model Router" in res_root.text
    print("  [PASS] GET / serves index.html UI correctly")

    res_css = client.get("/style.css")
    assert res_css.status_code == 200
    print("  [PASS] GET /style.css returns stylesheet")

    res_js = client.get("/app.js")
    assert res_js.status_code == 200
    print("  [PASS] GET /app.js returns client script")


if __name__ == "__main__":
    print("Starting Multi-Model Router Gateway Tests...")
    test_auth_workflow()
    test_model_inference()
    test_routing_scenarios()
    test_openai_compatible_endpoint()
    test_ui_endpoints()
    print("\nALL TESTS PASSED SUCCESSFULLY! Everything is working cleanly and correctly.")

