import os
import json
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, EvaluationRun, EvaluationResult, ModelBenchmarkConfig
from backend.routes.auth import get_admin_user, get_current_user, get_optional_user
from backend.services.evaluation_service import (
    evaluation_service,
    BENCHMARK_DATASET,
    PRICING_CONFIG,
    get_system_hardware_info
)

logger = logging.getLogger("evaluation_routes")

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


# Pydantic Request & Response Schemas
class SingleEvalRequest(BaseModel):
    prompt: str = Field(..., min_length=2, max_length=3000)
    expected_output: Optional[str] = None
    expected_scheme_id: Optional[str] = None
    expected_keywords: Optional[List[str]] = None
    parameters: Optional[Dict[str, Any]] = None
    language: Optional[str] = "auto"
    enable_rag: Optional[bool] = True
    test_case_id: Optional[str] = "CUSTOM-01"
    category: Optional[str] = "custom"


class BenchmarkRunRequest(BaseModel):
    name: Optional[str] = "Standard Maharashtra OBC Benchmark"
    dataset: Optional[List[Dict[str, Any]]] = None
    parameters: Optional[Dict[str, Any]] = None
    benchmark_type: Optional[str] = "standard"
    enable_rag: Optional[bool] = True
    repetitions: Optional[int] = Field(1, ge=1, le=5)
    warmup_requests: Optional[int] = Field(1, ge=0, le=3)


class ParameterSweepRequest(BaseModel):
    name: Optional[str] = "Multi-Parameter Comparison Experiment"
    parameter_configs: Optional[List[Dict[str, Any]]] = None
    subset_size: Optional[int] = Field(4, ge=2, le=16)


class AblationRequest(BaseModel):
    subset_size: Optional[int] = Field(5, ge=2, le=16)


class FeedbackRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = Field(None, max_length=1000)


@router.get("/model-info")
def get_model_information():
    """
    Return comprehensive, verified model configuration, supported parameters,
    context limits, and dated token pricing.
    """
    metadata = evaluation_service.get_model_metadata()
    system_info = get_system_hardware_info()
    return {
        "status": "ok",
        "model_metadata": metadata,
        "system_resources": system_info
    }


@router.get("/datasets")
def get_available_datasets():
    """
    List available evaluation benchmark datasets and summary statistics.
    """
    categories = {}
    languages = {}
    for tc in BENCHMARK_DATASET:
        cat = tc.get("category", "general")
        lang = tc.get("language", "en")
        categories[cat] = categories.get(cat, 0) + 1
        languages[lang] = languages.get(lang, 0) + 1

    return {
        "dataset_name": "Maharashtra OBC Education Benchmark v1.0",
        "total_test_cases": len(BENCHMARK_DATASET),
        "categories": categories,
        "languages": languages,
        "test_cases": BENCHMARK_DATASET
    }


@router.post("/run-single")
def run_single_evaluation(
    req: SingleEvalRequest,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Execute an on-demand, instrumented evaluation for a single prompt.
    Measures latency, TTFT, token consumption, RAG accuracy, and quality metrics.
    """
    try:
        result = evaluation_service.evaluate_single_request(
            prompt=req.prompt,
            expected_output=req.expected_output,
            expected_scheme_id=req.expected_scheme_id,
            expected_keywords=req.expected_keywords,
            parameters=req.parameters,
            language=req.language or "auto",
            enable_rag=req.enable_rag if req.enable_rag is not None else True,
            test_case_id=req.test_case_id or "MANUAL-01",
            category=req.category or "custom"
        )
        return result
    except Exception as e:
        logger.error(f"Single evaluation error: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.post("/run-benchmark")
def run_benchmark(
    req: BenchmarkRunRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Execute a full repeatable benchmark test run across curated or custom test cases.
    Persists evaluation run and all request-level metrics to the database.
    """
    try:
        user_id = current_user.id if current_user else None
        eval_run = evaluation_service.run_benchmark_suite(
            db=db,
            name=req.name or "Standard OBC Benchmark",
            dataset=req.dataset,
            parameters=req.parameters,
            benchmark_type=req.benchmark_type or "standard",
            enable_rag=req.enable_rag if req.enable_rag is not None else True,
            repetitions=req.repetitions or 1,
            warmup_requests=req.warmup_requests or 1,
            user_id=user_id
        )

        return {
            "status": "completed",
            "run_id": eval_run.id,
            "name": eval_run.name,
            "total_cases": eval_run.total_cases,
            "avg_latency_ms": eval_run.avg_latency_ms,
            "p50_latency_ms": eval_run.p50_latency_ms,
            "p95_latency_ms": eval_run.p95_latency_ms,
            "avg_ttft_ms": eval_run.avg_ttft_ms,
            "avg_tps": eval_run.avg_tps,
            "total_tokens": eval_run.total_tokens,
            "avg_quality_score": eval_run.avg_quality_score,
            "avg_faithfulness": eval_run.avg_faithfulness,
            "avg_semantic_similarity": eval_run.avg_semantic_similarity,
            "avg_exact_match": eval_run.avg_exact_match,
            "avg_f1": eval_run.avg_f1,
            "avg_rouge_l": eval_run.avg_rouge_l,
            "avg_bleu": eval_run.avg_bleu,
            "estimated_cost_usd": eval_run.estimated_cost_usd,
            "created_at": eval_run.created_at.isoformat() if eval_run.created_at else None
        }
    except Exception as e:
        logger.error(f"Benchmark execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Benchmark execution failed: {str(e)}")


@router.post("/run-experiment")
def run_parameter_experiment(
    req: ParameterSweepRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Run a controlled parameter sweep across multiple configurations and identify
    the best-performing setup for Lowest Latency, Highest Quality, Lowest Cost, and Balanced.
    """
    try:
        user_id = current_user.id if current_user else None
        res = evaluation_service.run_parameter_sweep_experiment(
            db=db,
            name=req.name or "Parameter Sweep Experiment",
            parameter_configs=req.parameter_configs,
            subset_size=req.subset_size or 4,
            user_id=user_id
        )
        return res
    except Exception as e:
        logger.error(f"Parameter experiment error: {e}")
        raise HTTPException(status_code=500, detail=f"Parameter sweep failed: {str(e)}")


@router.post("/run-ablation")
def run_ablation(
    req: AblationRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Run RAG vs No-RAG ablation test to quantify retrieval contribution to faithfulness,
    semantic accuracy, and response latency.
    """
    try:
        user_id = current_user.id if current_user else None
        res = evaluation_service.run_rag_ablation_comparison(
            db=db,
            subset_size=req.subset_size or 5,
            user_id=user_id
        )
        return res
    except Exception as e:
        logger.error(f"Ablation error: {e}")
        raise HTTPException(status_code=500, detail=f"Ablation test failed: {str(e)}")


@router.get("/runs")
def list_evaluation_runs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    benchmark_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List past benchmark runs with summary metrics, pagination, and filtering.
    """
    query = db.query(EvaluationRun)
    if benchmark_type:
        query = query.filter(EvaluationRun.benchmark_type == benchmark_type)

    total = query.count()
    runs = query.order_by(EvaluationRun.created_at.desc()).offset(skip).limit(limit).all()

    items = []
    for r in runs:
        items.append({
            "id": r.id,
            "name": r.name,
            "model_id": r.model_id,
            "provider": r.provider,
            "benchmark_type": r.benchmark_type,
            "status": r.status,
            "total_cases": r.total_cases,
            "successful_cases": r.successful_cases,
            "avg_latency_ms": r.avg_latency_ms,
            "p50_latency_ms": r.p50_latency_ms,
            "p95_latency_ms": r.p95_latency_ms,
            "avg_ttft_ms": r.avg_ttft_ms,
            "avg_tps": r.avg_tps,
            "total_tokens": r.total_tokens,
            "avg_quality_score": r.avg_quality_score,
            "avg_faithfulness": r.avg_faithfulness,
            "avg_semantic_similarity": r.avg_semantic_similarity,
            "avg_exact_match": r.avg_exact_match,
            "avg_f1": r.avg_f1,
            "avg_rouge_l": r.avg_rouge_l,
            "avg_bleu": r.avg_bleu,
            "estimated_cost_usd": r.estimated_cost_usd,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        })

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": items
    }


@router.get("/runs/{run_id}")
def get_evaluation_run_detail(
    run_id: str,
    db: Session = Depends(get_db)
):
    """
    Get complete details of a specific evaluation run along with all individual test case results.
    """
    run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found.")

    results = db.query(EvaluationResult).filter(EvaluationResult.run_id == run_id).order_by(EvaluationResult.created_at.asc()).all()

    result_items = []
    for r in results:
        result_items.append({
            "id": r.id,
            "test_case_id": r.test_case_id,
            "category": r.category,
            "prompt": r.prompt,
            "expected_output": r.expected_output,
            "expected_scheme_id": r.expected_scheme_id,
            "generated_response": r.generated_response,
            "detected_language": r.detected_language,
            "language_match": r.language_match,
            "status": r.status,
            "retrieval_latency_ms": r.retrieval_latency_ms,
            "generation_latency_ms": r.generation_latency_ms,
            "total_latency_ms": r.total_latency_ms,
            "ttft_ms": r.ttft_ms,
            "tokens_per_second": r.tokens_per_second,
            "prompt_tokens": r.prompt_tokens,
            "completion_tokens": r.completion_tokens,
            "total_tokens": r.total_tokens,
            "prompt_breakdown": json.loads(r.prompt_breakdown or "{}"),
            "context_window_utilization_pct": r.context_window_utilization_pct,
            "retrieved_chunks_count": r.retrieved_chunks_count,
            "retrieved_sources": json.loads(r.retrieved_sources or "[]"),
            "rag_precision_at_k": r.rag_precision_at_k,
            "rag_recall_at_k": r.rag_recall_at_k,
            "rag_mrr": r.rag_mrr,
            "exact_match": r.exact_match,
            "token_precision": r.token_precision,
            "token_recall": r.token_recall,
            "token_f1": r.token_f1,
            "rouge_l": r.rouge_l,
            "bleu_1": r.bleu_1,
            "bleu_4": r.bleu_4,
            "semantic_similarity": r.semantic_similarity,
            "faithfulness": r.faithfulness,
            "answer_relevance": r.answer_relevance,
            "hallucination_detected": r.hallucination_detected,
            "human_rating": r.human_rating,
            "human_feedback": r.human_feedback,
            "estimated_cost_usd": r.estimated_cost_usd,
            "created_at": r.created_at.isoformat() if r.created_at else None
        })

    return {
        "run": {
            "id": run.id,
            "name": run.name,
            "model_id": run.model_id,
            "provider": run.provider,
            "dataset_name": run.dataset_name,
            "benchmark_type": run.benchmark_type,
            "parameters": json.loads(run.parameters or "{}"),
            "status": run.status,
            "total_cases": run.total_cases,
            "successful_cases": run.successful_cases,
            "failed_cases": run.failed_cases,
            "avg_latency_ms": run.avg_latency_ms,
            "p50_latency_ms": run.p50_latency_ms,
            "p90_latency_ms": run.p90_latency_ms,
            "p95_latency_ms": run.p95_latency_ms,
            "min_latency_ms": run.min_latency_ms,
            "max_latency_ms": run.max_latency_ms,
            "avg_ttft_ms": run.avg_ttft_ms,
            "avg_tps": run.avg_tps,
            "total_prompt_tokens": run.total_prompt_tokens,
            "total_completion_tokens": run.total_completion_tokens,
            "total_tokens": run.total_tokens,
            "avg_quality_score": run.avg_quality_score,
            "avg_faithfulness": run.avg_faithfulness,
            "avg_exact_match": run.avg_exact_match,
            "avg_f1": run.avg_f1,
            "avg_rouge_l": run.avg_rouge_l,
            "avg_bleu": run.avg_bleu,
            "avg_semantic_similarity": run.avg_semantic_similarity,
            "estimated_cost_usd": run.estimated_cost_usd,
            "system_info": json.loads(run.system_info or "{}"),
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None
        },
        "results": result_items
    }


@router.get("/runs/{run_id}/export")
def export_evaluation_run(
    run_id: str,
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db)
):
    """
    Export benchmark run and results to downloadable CSV or JSON file.
    """
    try:
        content, media_type = evaluation_service.export_run_data(db=db, run_id=run_id, format_type=format)
        filename = f"llm_evaluation_run_{run_id}.{format.lower()}"
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/results/{result_id}/feedback")
def submit_human_feedback(
    result_id: str,
    req: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Submit human review feedback or quality rating (1 to 5 stars) for an evaluated response.
    """
    res = db.query(EvaluationResult).filter(EvaluationResult.id == result_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Evaluation result not found.")

    res.human_rating = req.rating
    if req.feedback:
        res.human_feedback = req.feedback

    db.commit()
    db.refresh(res)
    return {
        "status": "success",
        "result_id": res.id,
        "human_rating": res.human_rating,
        "human_feedback": res.human_feedback
    }
