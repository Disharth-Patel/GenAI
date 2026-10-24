import re
import json
import time
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Conversation, Message
from backend.routes.auth import get_current_user, get_optional_user
from backend.services.retrieval_service import retriever
from backend.services.ai_service import ai_service

logger = logging.getLogger("chat_route")

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None
    language: Optional[str] = "auto"


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    language: str
    sources: List[Dict[str, Any]]
    metrics: Optional[Dict[str, Any]] = None


class MessageOut(BaseModel):
    id: str
    role: str
    text: str
    sources: Optional[List[Dict[str, Any]]] = None
    language: str
    created_at: str


class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class ConversationDetailOut(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[MessageOut]


@router.post("/chat", response_model=ChatResponse)
def handle_chat(
    req: ChatRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Generate an AI response using RAG retrieval over Maharashtra OBC knowledge base.
    Persists history to conversation if user is authenticated or conversation exists.
    """
    clean_msg = req.message.strip()
    if not clean_msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Find or create conversation
    conversation = None
    if req.conversation_id:
        conversation = db.query(Conversation).filter(Conversation.id == req.conversation_id).first()
        if conversation:
            # If conversation has an owner and an authenticated user is calling, enforce ownership
            if current_user and conversation.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="Access denied to this conversation.")

    if not conversation:
        owner_id = current_user.id if current_user else None
        if not owner_id:
            default_student = db.query(User).filter(User.username == "student").first()
            owner_id = default_student.id if default_student else None

        title_snippet = clean_msg[:40] + ("..." if len(clean_msg) > 40 else "")
        conversation = Conversation(
            user_id=owner_id,
            title=title_snippet
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # 1. Fetch past conversation history
    history_messages = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.created_at.asc()).limit(8).all()

    conv_history = [{"role": m.role, "text": m.text} for m in history_messages]

    # 2. Formulate context-aware retrieval query across language switches
    search_query = clean_msg
    anaphoric_markers = {
        "this", "it", "that", "these", "those", "here", "there", "scheme", "scholarship",
        "iska", "iski", "iske", "isme", "ismein", "yaha", "ye", "yeh", "kya", "kab", "kaise",
        "kitna", "kitni", "batao", "bataye", "rules", "rule", "criteria", "eligibility",
        "यासाठी", "यात", "ह्या", "या", "तिचे", "त्याची", "त्यासाठी", "योजना", "अटी", "नियम"
    }
    msg_words = set(re.findall(r"\w+", clean_msg.lower()))
    if conv_history and (len(msg_words) <= 8 or msg_words.intersection(anaphoric_markers)):
        # Extract meaningful context tokens from last 2 messages
        last_context = " ".join([m["text"] for m in conv_history[-2:]])
        clean_context = re.sub(r"\[.*?\]\(.*?\)|###|\*\*|_", " ", last_context)
        context_words = [w for w in re.findall(r"\w+", clean_context) if len(w) > 3][:12]
        if context_words:
            search_query = f"{clean_msg} {' '.join(context_words)}"

    # 3. Retrieve knowledge from RAG vector/hybrid index
    t_start = time.perf_counter()
    retrieved_chunks = retriever.search(query=search_query, top_k=5)

    # 3. Generate answer via AI service
    try:
        answer, effective_lang, sources = ai_service.generate_chat_response(
            message=clean_msg,
            retrieved_sources=retrieved_chunks,
            requested_language=req.language or "auto",
            conversation_history=conv_history,
        )
    except RuntimeError as exc:
        logger.error("Local Ollama inference failed: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    latency_ms = round((time.perf_counter() - t_start) * 1000, 2)

    last_m = getattr(ai_service, "last_metrics", None)
    if last_m and last_m.get("total_tokens"):
        latency_ms = last_m.get("latency_ms", latency_ms)
        input_tokens_est = last_m.get("prompt_tokens", 0)
        output_tokens_est = last_m.get("completion_tokens", 0)
        total_tokens_est = last_m.get("total_tokens", input_tokens_est + output_tokens_est)
        tps = last_m.get("tokens_per_second", 0.0)
        cost_est_usd = 0.0  # Zero cost for local open-weight inference
        model_name = last_m.get("model", ai_service.model_name)
        provider_name = last_m.get("provider", "ollama")
    else:
        input_tokens_est = max(1, int(len(clean_msg.split()) * 1.35) + sum(int(len(s.get("content", "").split()) * 1.3) for s in sources[:3]))
        output_tokens_est = max(1, int(len(answer.split()) * 1.35))
        total_tokens_est = input_tokens_est + output_tokens_est
        tps = round(output_tokens_est / max(0.001, latency_ms / 1000.0), 2)
        cost_est_usd = 0.0 if ai_service.provider == "ollama" else round((input_tokens_est * 0.000000075) + (output_tokens_est * 0.0000003), 6)
        model_name = getattr(ai_service, "model_name", "llama3.2:latest")
        provider_name = getattr(ai_service, "provider", "ollama")

    metrics = {
        "latency_ms": latency_ms,
        "input_tokens_est": input_tokens_est,
        "output_tokens_est": output_tokens_est,
        "total_tokens_est": total_tokens_est,
        "tokens_per_second": tps,
        "cost_est_usd": cost_est_usd,
        "model": model_name,
        "provider": provider_name,
        "retrieved_count": len(sources)
    }

    # 4. Save User Message
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        text=clean_msg,
        language=effective_lang,
    )
    db.add(user_msg)

    # 5. Save Assistant Message
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        text=answer,
        sources=json.dumps(sources) if sources else None,
        language=effective_lang,
    )
    db.add(assistant_msg)

    # Update conversation timestamp using explicit UTC timestamp
    from datetime import datetime, timezone
    conversation.updated_at = datetime.now(timezone.utc)
    db.commit()

    return ChatResponse(
        answer=answer,
        conversation_id=conversation.id,
        language=effective_lang,
        sources=sources,
        metrics=metrics
    )


@router.get("/conversations", response_model=List[ConversationOut])
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List conversations belonging to the current user."""
    convs = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).all()

    return [
        ConversationOut(
            id=c.id,
            title=c.title,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat()
        )
        for c in convs
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailOut)
def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve full message history of a conversation (owner only)."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    if conv.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation.")

    messages_out = []
    for m in conv.messages:
        parsed_sources = None
        if m.sources:
            try:
                parsed_sources = json.loads(m.sources)
            except Exception:
                parsed_sources = None

        messages_out.append(MessageOut(
            id=m.id,
            role=m.role,
            text=m.text,
            sources=parsed_sources,
            language=m.language,
            created_at=m.created_at.isoformat()
        ))

    return ConversationDetailOut(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at.isoformat(),
        updated_at=conv.updated_at.isoformat(),
        messages=messages_out
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation (owner only)."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    if conv.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this conversation.")

    db.delete(conv)
    db.commit()
    return None


@router.get("/llm/status")
def get_llm_runtime_status():
    """Check Ollama runtime health, active model, installed models, and hardware metrics."""
    from backend.services.ollama_service import ollama_service
    from backend.services.evaluation_service import get_system_hardware_info

    health = ollama_service.check_health()
    hardware = get_system_hardware_info()
    return {
        "status": "ok",
        "provider": ai_service.provider,
        "health": health,
        "active_model": ai_service.model_name,
        "hardware": hardware,
        "setup_guide": {
            "install_url": "https://ollama.com/download/windows",
            "pull_command": f"ollama pull {ollama_service.model_name}",
            "run_command": f"ollama run {ollama_service.model_name}"
        }
    }
