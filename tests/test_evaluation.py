import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.evaluation_service import (
    calculate_exact_match,
    calculate_token_f1,
    calculate_rouge_l,
    calculate_bleu,
    calculate_semantic_similarity,
    calculate_faithfulness,
    count_tokens_calibrated,
    calculate_cost
)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_evaluation_metrics_calculations():
    """Verify mathematical correctness of NLP and generation quality metrics."""
    ref = "Applicant must belong to OBC and have income under 2.5 lakh."
    cand_identical = "Applicant must belong to OBC and have income under 2.5 lakh."
    cand_partial = "OBC applicant with income below 2.5 lakh."
    cand_different = "Driving licenses are issued by the regional transport authority."

    # 1. Exact Match
    assert calculate_exact_match(cand_identical, ref) == 1.0
    assert calculate_exact_match(cand_partial, ref) == 0.0

    # 2. Token Precision, Recall, F1
    p, r, f1 = calculate_token_f1(cand_identical, ref)
    assert p == 1.0 and r == 1.0 and f1 == 1.0
    p2, r2, f1_partial = calculate_token_f1(cand_partial, ref)
    assert 0.0 < f1_partial < 1.0
    p3, r3, f1_diff = calculate_token_f1(cand_different, ref)
    assert f1_diff == 0.0

    # 3. ROUGE-L
    rouge_identical = calculate_rouge_l(cand_identical, ref)
    assert rouge_identical == 1.0
    rouge_partial = calculate_rouge_l(cand_partial, ref)
    assert 0.0 < rouge_partial < 1.0

    # 4. BLEU-1 and BLEU-4
    b1, b4 = calculate_bleu(cand_identical, ref)
    assert b1 == 1.0
    assert b4 > 0.8

    # 5. Semantic Similarity
    sim_identical = calculate_semantic_similarity(cand_identical, ref)
    assert sim_identical > 0.95
    sim_different = calculate_semantic_similarity(cand_different, ref)
    assert sim_different < 0.2

    # 6. Faithfulness / Groundedness
    context = ["Applicant must belong to OBC category and have family income under 2.5 lakh per year."]
    faith_grounded = calculate_faithfulness(cand_identical, context)
    assert faith_grounded > 0.7
    faith_hallucinated = calculate_faithfulness(cand_different, context)
    assert faith_hallucinated < 0.3

    # 7. Token counting
    en_tokens = count_tokens_calibrated("What is the post matric scholarship?")
    assert 4 <= en_tokens <= 12
    mr_tokens = count_tokens_calibrated("ओबीसी विद्यार्थ्यांसाठी शिष्यवृत्ती योजना काय आहे?")
    assert mr_tokens > 5

    # 8. Cost calculation
    cost = calculate_cost(1000, 500, "gemini-2.5-flash")
    assert cost > 0.0


def test_model_info_endpoint(client):
    """Verify model metadata endpoint returns verifiable configuration and parameters."""
    res = client.get("/api/evaluation/model-info")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    meta = data["model_metadata"]
    assert "model_provider" in meta
    assert "model_name" in meta
    assert "max_context_window" in meta
    assert "supported_parameters" in meta
    assert "temperature" in meta["supported_parameters"]
    assert "top_p" in meta["supported_parameters"]
    assert "system_resources" in data
    assert "ram_total_mb" in data["system_resources"]


def test_datasets_endpoint(client):
    """Verify built-in evaluation dataset endpoint."""
    res = client.get("/api/evaluation/datasets")
    assert res.status_code == 200
    data = res.json()
    assert data["total_test_cases"] >= 10
    assert "categories" in data
    assert "scholarship" in data["categories"]
    assert len(data["test_cases"]) > 0


def test_single_evaluation_endpoint(client):
    """Verify single prompt evaluation with RAG retrieval and metric computation."""
    payload = {
        "prompt": "What are the eligibility criteria for Post Matric Scholarship to OBC Students in Maharashtra?",
        "expected_output": "Applicant must belong to OBC category with annual family income up to ₹2.50 lakh.",
        "expected_scheme_id": "OBC-001",
        "expected_keywords": ["OBC", "income", "scholarship", "MahaDBT"],
        "parameters": {"temperature": 0.2, "max_output_tokens": 500},
        "enable_rag": True,
        "language": "en"
    }
    res = client.post("/api/evaluation/run-single", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert "generated_response" in data
    assert len(data["generated_response"]) > 20
    assert data["status"] == "success"
    assert data["total_latency_ms"] > 0
    assert data["tokens_per_second"] >= 0
    assert data["prompt_tokens"] > 0
    assert data["completion_tokens"] > 0
    assert "prompt_breakdown" in data
    assert "system_tokens" in data["prompt_breakdown"]
    assert "faithfulness" in data
    assert "token_f1" in data
    assert "rouge_l" in data
    assert "semantic_similarity" in data


def test_benchmark_suite_execution_and_persistence(client):
    """Verify executing benchmark suite persists run and results in database."""
    custom_dataset = [
        {
            "id": "TC-TEST-1",
            "category": "scholarship",
            "prompt": "Tell me about the Post Matric Scholarship for OBC in Maharashtra.",
            "expected_output": "Post matric scholarship for OBC students.",
            "expected_scheme_id": "OBC-001",
            "language": "en"
        },
        {
            "id": "TC-TEST-2",
            "category": "hostel",
            "prompt": "ज्ञानज्योती सावित्रीबाई फुले वसतिगृह आधार योजना काय आहे?",
            "expected_output": "वसतिगृह भत्ता योजना.",
            "expected_scheme_id": "OBC-007",
            "language": "mr"
        }
    ]

    payload = {
        "name": "Automated Unit Test Benchmark",
        "dataset": custom_dataset,
        "parameters": {"temperature": 0.3},
        "repetitions": 1,
        "warmup_requests": 0,
        "enable_rag": True
    }
    res = client.post("/api/evaluation/run-benchmark", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "completed"
    assert data["total_cases"] == 2
    assert "run_id" in data
    run_id = data["run_id"]
    assert data["avg_latency_ms"] > 0
    assert data["p95_latency_ms"] >= data["p50_latency_ms"]

    # Verify run details retrieval
    detail_res = client.get(f"/api/evaluation/runs/{run_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["run"]["id"] == run_id
    assert len(detail["results"]) == 2
    assert detail["results"][0]["test_case_id"] == "TC-TEST-1"

    # Verify listing runs includes this run
    list_res = client.get("/api/evaluation/runs?limit=10")
    assert list_res.status_code == 200
    runs_list = list_res.json()
    assert runs_list["total"] >= 1
    assert any(r["id"] == run_id for r in runs_list["items"])


def test_parameter_experiment_sweep(client):
    """Verify parameter sweep comparison and objective recommendations."""
    payload = {
        "name": "Test Temperature Sweep",
        "parameter_configs": [
            {"name": "Deterministic Low Temp", "temperature": 0.0, "max_output_tokens": 400},
            {"name": "Balanced Mid Temp", "temperature": 0.3, "max_output_tokens": 400}
        ],
        "subset_size": 2
    }
    res = client.post("/api/evaluation/run-experiment", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["configurations_evaluated"] == 2
    assert "recommendations" in data
    assert "lowest_latency" in data["recommendations"]
    assert "highest_quality" in data["recommendations"]
    assert "best_balanced" in data["recommendations"]


def test_rag_ablation_comparison(client):
    """Verify RAG vs No-RAG ablation test endpoint."""
    res = client.post("/api/evaluation/run-ablation", json={"subset_size": 2})
    assert res.status_code == 200
    data = res.json()
    assert data["comparison_type"] == "rag_ablation"
    assert "rag_enabled_run" in data
    assert "no_rag_run" in data
    assert "insights" in data
    assert "faithfulness_delta" in data["insights"]


def test_export_benchmark_run_csv_and_json(client):
    """Verify benchmark run data export in CSV and JSON formats."""
    # Create a small run first
    test_ds = [{
        "id": "TC-EXP-1",
        "category": "test",
        "prompt": "Test export prompt",
        "expected_output": "Test export output"
    }]
    run_res = client.post("/api/evaluation/run-benchmark", json={
        "name": "Export Test Run",
        "dataset": test_ds,
        "warmup_requests": 0
    })
    run_id = run_res.json()["run_id"]

    # Export JSON
    json_res = client.get(f"/api/evaluation/runs/{run_id}/export?format=json")
    assert json_res.status_code == 200
    assert "application/json" in json_res.headers["content-type"]
    exported_json = json_res.json()
    assert exported_json["run_id"] == run_id
    assert len(exported_json["results"]) == 1

    # Export CSV
    csv_res = client.get(f"/api/evaluation/runs/{run_id}/export?format=csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    csv_text = csv_res.text
    assert "result_id,test_case_id" in csv_text
    assert "TC-EXP-1" in csv_text


def test_human_feedback_submission(client):
    """Verify submitting human reviewer star rating and comments."""
    test_ds = [{
        "id": "TC-FEEDBACK-1",
        "category": "test",
        "prompt": "Sample query for feedback",
        "expected_output": "Sample output"
    }]
    run_res = client.post("/api/evaluation/run-benchmark", json={
        "name": "Feedback Test Run",
        "dataset": test_ds,
        "warmup_requests": 0
    })
    run_id = run_res.json()["run_id"]
    detail = client.get(f"/api/evaluation/runs/{run_id}").json()
    result_id = detail["results"][0]["id"]

    # Submit 5-star review
    fb_res = client.post(f"/api/evaluation/results/{result_id}/feedback", json={
        "rating": 5,
        "feedback": "Extremely accurate grounded response with verified official links."
    })
    assert fb_res.status_code == 200
    fb_data = fb_res.json()
    assert fb_data["status"] == "success"
    assert fb_data["human_rating"] == 5

    # Verify updated in run details
    detail_after = client.get(f"/api/evaluation/runs/{run_id}").json()
    assert detail_after["results"][0]["human_rating"] == 5
    assert "Extremely accurate" in detail_after["results"][0]["human_feedback"]
