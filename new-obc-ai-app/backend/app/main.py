from fastapi import FastAPI, Depends
from app.core.config import settings
from app.api.chat_routes import router as chat_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Professional RAG-powered Voice AI Chatbot for Maharashtra OBC Education Schemes",
    version="1.0.0"
)

# Include Routers
app.include_router(chat_router)

@app.get("/health")
async def health_check():
    """Health check to verify the API and Ollama connectivity."""
    from app.services.ollama_service import ollama_service
    ollama_ok = await ollama_service.check_health()
    return {
        "status": "ok" if ollama_ok else "degraded",
        "ollama_connectivity": ollama_ok,
        "model": settings.OLLAMA_MODEL
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
