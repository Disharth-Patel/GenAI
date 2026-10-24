import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float, Boolean
from sqlalchemy.orm import relationship
from backend.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="student", nullable=False)  # "admin" or "student"
    created_at = Column(DateTime, default=utc_now, nullable=False)

    conversations = relationship("Conversation", back_populates="owner", cascade="all, delete-orphan")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    title = Column(String(255), default="New Chat", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    owner = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user", "assistant", "system"
    text = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)  # JSON-serialized list of sources
    language = Column(String(20), default="en", nullable=False)
    audio_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")


class KnowledgeEntry(Base):
    __tablename__ = "knowledge_entries"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    knowledge_id = Column(String(64), index=True, nullable=True)  # e.g., "OBC-001", "FAQ-012"
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)
    retrieval_text = Column(Text, nullable=False)
    record_type = Column(String(50), default="scheme", index=True, nullable=False)  # "scheme", "faq", "guide", "glossary", "source_directory"
    category = Column(String(100), default="education_scheme", index=True, nullable=False)
    scheme_id = Column(String(64), nullable=True, index=True)

    official_source = Column(String(1000), nullable=True)
    source_quality = Column(String(50), default="official", nullable=False)  # "official", "provisional", "needs verification"
    data_status = Column(String(50), default="verified", nullable=False)
    seat_capacity = Column(String(500), nullable=True)
    validity_notes = Column(Text, nullable=True)
    response_disclaimer = Column(Text, nullable=True)

    keywords = Column(Text, nullable=True)
    multilingual_terms = Column(Text, nullable=True)
    query_variants = Column(Text, nullable=True)

    source_type = Column(String(50), default="dataset", nullable=False)  # "dataset", "manual", "upload"
    source_filename = Column(String(255), nullable=True)
    indexing_status = Column(String(50), default="indexed", nullable=False)  # "indexed", "pending", "failed"
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    model_id = Column(String(100), nullable=False, default="gemini-2.5-flash")
    provider = Column(String(50), nullable=False, default="gemini")
    dataset_name = Column(String(100), default="maharashtra_obc_standard")
    benchmark_type = Column(String(50), default="standard")  # standard, parameter_sweep, ablation, custom
    parameters = Column(Text, nullable=True)  # JSON-encoded parameters
    status = Column(String(30), default="completed", nullable=False)  # running, completed, failed

    total_cases = Column(Integer, default=0, nullable=False)
    successful_cases = Column(Integer, default=0, nullable=False)
    failed_cases = Column(Integer, default=0, nullable=False)

    avg_latency_ms = Column(Float, default=0.0)
    p50_latency_ms = Column(Float, default=0.0)
    p90_latency_ms = Column(Float, default=0.0)
    p95_latency_ms = Column(Float, default=0.0)
    min_latency_ms = Column(Float, default=0.0)
    max_latency_ms = Column(Float, default=0.0)
    avg_ttft_ms = Column(Float, nullable=True)
    avg_tps = Column(Float, default=0.0)

    total_prompt_tokens = Column(Integer, default=0)
    total_completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)

    avg_quality_score = Column(Float, default=0.0)
    avg_faithfulness = Column(Float, default=0.0)
    avg_exact_match = Column(Float, default=0.0)
    avg_f1 = Column(Float, default=0.0)
    avg_rouge_l = Column(Float, default=0.0)
    avg_bleu = Column(Float, default=0.0)
    avg_semantic_similarity = Column(Float, default=0.0)
    estimated_cost_usd = Column(Float, default=0.0)
    system_info = Column(Text, nullable=True)  # JSON-encoded system specs (CPU, RAM)

    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    results = relationship(
        "EvaluationResult",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="EvaluationResult.created_at"
    )


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("evaluation_runs.id"), nullable=False, index=True)
    test_case_id = Column(String(64), nullable=True, index=True)
    category = Column(String(100), default="general", index=True)
    prompt = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=True)
    expected_scheme_id = Column(String(64), nullable=True)
    generated_response = Column(Text, nullable=False)
    detected_language = Column(String(20), default="en")
    language_match = Column(Boolean, default=True)

    status = Column(String(20), default="success")  # success, error, timeout
    error_message = Column(Text, nullable=True)
    parameters = Column(Text, nullable=True)  # JSON string

    retrieval_latency_ms = Column(Float, default=0.0)
    generation_latency_ms = Column(Float, default=0.0)
    total_latency_ms = Column(Float, default=0.0)
    ttft_ms = Column(Float, nullable=True)
    tokens_per_second = Column(Float, default=0.0)

    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    prompt_breakdown = Column(Text, nullable=True)  # JSON
    context_window_utilization_pct = Column(Float, default=0.0)

    retrieved_chunks_count = Column(Integer, default=0)
    retrieved_sources = Column(Text, nullable=True)  # JSON
    rag_precision_at_k = Column(Float, nullable=True)
    rag_recall_at_k = Column(Float, nullable=True)
    rag_mrr = Column(Float, nullable=True)

    exact_match = Column(Float, default=0.0)
    token_precision = Column(Float, default=0.0)
    token_recall = Column(Float, default=0.0)
    token_f1 = Column(Float, default=0.0)
    rouge_l = Column(Float, default=0.0)
    bleu_1 = Column(Float, default=0.0)
    bleu_4 = Column(Float, default=0.0)
    semantic_similarity = Column(Float, default=0.0)
    faithfulness = Column(Float, default=0.0)
    answer_relevance = Column(Float, default=0.0)
    hallucination_detected = Column(Boolean, default=False)

    human_rating = Column(Integer, nullable=True)  # 1 to 5
    human_feedback = Column(Text, nullable=True)
    estimated_cost_usd = Column(Float, default=0.0)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    run = relationship("EvaluationRun", back_populates="results")


class ModelBenchmarkConfig(Base):
    __tablename__ = "model_benchmark_configs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500), nullable=True)
    temperature = Column(Float, default=0.3)
    top_p = Column(Float, default=0.95)
    top_k = Column(Integer, default=40)
    max_output_tokens = Column(Integer, default=1000)
    stop_sequences = Column(String(500), nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

