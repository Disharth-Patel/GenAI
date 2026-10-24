import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.database import init_db, SessionLocal
from backend.routes.auth import router as auth_router, seed_default_admin
from backend.routes.chat import router as chat_router
from backend.routes.speech import router as speech_router
from backend.routes.knowledge import router as knowledge_router
from backend.routes.evaluation import router as evaluation_router
from backend.services.retrieval_service import seed_knowledge_from_csv
from backend.models import KnowledgeEntry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("backend_main")

APP_NAME = os.getenv("APP_NAME", "Maharashtra OBC Education Voice AI Chatbot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info(f"Starting {APP_NAME}...")
    # Initialize database tables
    init_db()

    # Seed admin user and knowledge base if needed
    db = SessionLocal()
    try:
        seed_default_admin(db)
        seed_knowledge_from_csv(db)
    finally:
        db.close()

    logger.info("Application startup completed successfully.")
    yield
    logger.info("Application shutting down.")


app = FastAPI(
    title=APP_NAME,
    description="Full-Stack Voice AI Chatbot with Multilingual RAG for Maharashtra OBC Education Schemes",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Development configuration
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public Health Endpoint
@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint required by Phase A."""
    db = SessionLocal()
    try:
        count = db.query(KnowledgeEntry).count()
    except Exception:
        count = 0
    finally:
        db.close()

    return {
        "status": "ok",
        "app": APP_NAME,
        "version": "1.0.0",
        "indexed_knowledge_entries": count
    }


# Include Routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(speech_router)
app.include_router(knowledge_router)
app.include_router(evaluation_router)

# Mount frontend directory at root if it exists (placed after all API routers)
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.isdir(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
