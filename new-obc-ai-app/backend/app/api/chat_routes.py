from fastapi import APIRouter, Depends, HTTPException
from typing import List
import uuid

from app.schemas.chat import ChatRequest, ChatResponse, SourceCitation
from app.services.ollama_service import ollama_service
from app.services.retrieval_service import retrieval_service

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    RAG-powered chat endpoint that retrieves context from
    the local vector store before generating a response via Ollama.
    """
    # 1. Retrieve relevant context from the Knowledge Base
    context_docs = await retrieval_service.retrieve_context(request.message)

    # 2. Construct the grounded prompt
    context_text = "\n\n".join([
        f"Source {i+1}: {doc['text']}"
        for i, doc in enumerate(context_docs)
    ])

    system_prompt = (
        "You are a helpful and professional assistant specializing in Maharashtra OBC Education Schemes. "
        "Use the provided context to answer the user's question. "
        "If the answer is not contained within the context, honestly state that you do not have "
        "that specific information, but offer to help with related scholarship or hostel queries. "
        "Always maintain a polite and supportive tone. "
        "Answer in the language requested by the user."
    )

    full_prompt = (
        f"CONTEXT:\n{context_text}\n\n"
        f"USER QUESTION: {request.message}\n\n"
        f"Please provide a detailed and accurate answer based on the context above."
    )

    # 3. Generate response via local Ollama LLM
    try:
        answer = await ollama_service.generate_response(
            prompt=full_prompt,
            system_prompt=system_prompt
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Generation failed: {str(e)}")

    # 4. Map sources for citations
    sources = [
        SourceCitation(text=doc['text'], metadata=doc['metadata'], id=doc['id'])
        for doc in context_docs
    ]

    return ChatResponse(
        answer=answer,
        conversation_id=str(uuid.uuid4()),
        sources=sources
    )
