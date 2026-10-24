from pydantic import BaseModel, Field
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None
    language: str = "en"

class SourceCitation(BaseModel):
    text: str
    metadata: dict
    id: str

class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    sources: List[SourceCitation] = []
