import os
import uuid
import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, KnowledgeEntry
from backend.routes.auth import get_admin_user, get_current_user
from backend.services.retrieval_service import retriever, reload_retriever_from_db, seed_knowledge_from_csv

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "knowledge/uploads")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "15"))
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".csv", ".xlsx"}


# Pydantic Schemas
class KnowledgeEntryCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=500)
    content: str = Field(..., min_length=5)
    retrieval_text: Optional[str] = None
    record_type: Optional[str] = "scheme"
    category: Optional[str] = "education_scheme"
    scheme_id: Optional[str] = None
    official_source: Optional[str] = None
    source_quality: Optional[str] = "official"
    data_status: Optional[str] = "verified"
    seat_capacity: Optional[str] = None
    validity_notes: Optional[str] = None
    response_disclaimer: Optional[str] = None
    keywords: Optional[str] = None
    multilingual_terms: Optional[str] = None
    query_variants: Optional[str] = None


class KnowledgeEntryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    retrieval_text: Optional[str] = None
    record_type: Optional[str] = None
    category: Optional[str] = None
    scheme_id: Optional[str] = None
    official_source: Optional[str] = None
    source_quality: Optional[str] = None
    data_status: Optional[str] = None
    seat_capacity: Optional[str] = None
    validity_notes: Optional[str] = None
    response_disclaimer: Optional[str] = None
    keywords: Optional[str] = None
    multilingual_terms: Optional[str] = None
    query_variants: Optional[str] = None


class KnowledgeEntryOut(BaseModel):
    id: str
    knowledge_id: Optional[str] = None
    title: str
    content: str
    retrieval_text: Optional[str] = None
    record_type: str
    category: str
    scheme_id: Optional[str] = None
    official_source: Optional[str] = None
    source_quality: str
    data_status: str
    seat_capacity: Optional[str] = None
    validity_notes: Optional[str] = None
    response_disclaimer: Optional[str] = None
    keywords: Optional[str] = None
    multilingual_terms: Optional[str] = None
    query_variants: Optional[str] = None
    source_type: str
    source_filename: Optional[str] = None
    indexing_status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    model_config = {"from_attributes": True}


@router.get("", response_model=Dict[str, Any])
def list_knowledge(
    q: Optional[str] = Query(None, description="Search query"),
    record_type: Optional[str] = Query(None, description="Filter by record_type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Search and list knowledge entries. Admin only."""
    query = db.query(KnowledgeEntry)

    if record_type:
        query = query.filter(KnowledgeEntry.record_type == record_type)
    if category:
        query = query.filter(KnowledgeEntry.category == category)
    if q:
        search_pattern = f"%{q.strip()}%"
        query = query.filter(
            (KnowledgeEntry.title.ilike(search_pattern)) |
            (KnowledgeEntry.content.ilike(search_pattern)) |
            (KnowledgeEntry.keywords.ilike(search_pattern)) |
            (KnowledgeEntry.multilingual_terms.ilike(search_pattern))
        )

    total = query.count()
    items = query.order_by(KnowledgeEntry.updated_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": [KnowledgeEntryOut.model_validate(item) for item in items],
        "skip": skip,
        "limit": limit
    }


@router.post("", response_model=KnowledgeEntryOut, status_code=status.HTTP_201_CREATED)
def create_knowledge_entry(
    entry_in: KnowledgeEntryCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Create a new knowledge entry and immediately update retrieval index."""
    retrieval_text = entry_in.retrieval_text or f"{entry_in.title}. {entry_in.content}"

    entry = KnowledgeEntry(
        id=str(uuid.uuid4()),
        knowledge_id=f"MANUAL-{str(uuid.uuid4())[:8].upper()}",
        title=entry_in.title.strip(),
        content=entry_in.content.strip(),
        retrieval_text=retrieval_text.strip(),
        record_type=entry_in.record_type or "scheme",
        category=entry_in.category or "education_scheme",
        scheme_id=entry_in.scheme_id,
        official_source=entry_in.official_source,
        source_quality=entry_in.source_quality or "official",
        data_status=entry_in.data_status or "verified",
        seat_capacity=entry_in.seat_capacity,
        validity_notes=entry_in.validity_notes,
        response_disclaimer=entry_in.response_disclaimer,
        keywords=entry_in.keywords,
        multilingual_terms=entry_in.multilingual_terms,
        query_variants=entry_in.query_variants,
        source_type="manual",
        indexing_status="indexed"
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    # Synchronize index
    reload_retriever_from_db(db)

    return KnowledgeEntryOut.model_validate(entry)


@router.get("/{entry_id}", response_model=KnowledgeEntryOut)
def get_knowledge_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Retrieve single knowledge entry by ID."""
    entry = db.query(KnowledgeEntry).filter(KnowledgeEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found.")
    return KnowledgeEntryOut.model_validate(entry)


@router.put("/{entry_id}", response_model=KnowledgeEntryOut)
def update_knowledge_entry(
    entry_id: str,
    update_in: KnowledgeEntryUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Update a knowledge entry and re-index in retriever."""
    entry = db.query(KnowledgeEntry).filter(KnowledgeEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found.")

    update_data = update_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if val is not None:
            setattr(entry, field, val)

    if "title" in update_data or "content" in update_data:
        if not update_in.retrieval_text:
            entry.retrieval_text = f"{entry.title}. {entry.content}"

    db.commit()
    db.refresh(entry)

    # Synchronize index
    reload_retriever_from_db(db)

    return KnowledgeEntryOut.model_validate(entry)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Delete a knowledge entry and invalidate its index entries."""
    entry = db.query(KnowledgeEntry).filter(KnowledgeEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found.")

    db.delete(entry)
    db.commit()

    # Synchronize index
    reload_retriever_from_db(db)
    return None


def extract_text_from_file(file_path: str, ext: str) -> str:
    """Extract clean text content from supported file types."""
    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    elif ext == ".pdf":
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            pages = [page.get_text() for page in doc]
            return "\n".join(pages)
        except Exception:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            return "\n".join([page.extract_text() or "" for page in reader.pages])

    elif ext == ".docx":
        import docx
        doc = docx.Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)

    elif ext == ".csv":
        import pandas as pd
        df = pd.read_csv(file_path, encoding="utf-8", on_bad_lines="skip")
        return df.to_string(index=False)

    elif ext == ".xlsx":
        import pandas as pd
        excel = pd.ExcelFile(file_path)
        sheets_text = []
        for sheet_name in excel.sheet_names:
            df = excel.parse(sheet_name)
            sheets_text.append(f"--- Sheet: {sheet_name} ---\n" + df.to_string(index=False))
        return "\n\n".join(sheets_text)

    return ""


@router.post("/upload", response_model=Dict[str, Any])
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    category: Optional[str] = Form("uploaded_document"),
    record_type: Optional[str] = Form("guide"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Upload a document (PDF, DOCX, TXT, CSV, XLSX), parse, extract text,
    create knowledge entries, and synchronize retrieval index.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = file.filename or "uploaded_doc"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read contents and check size
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum upload size of {MAX_UPLOAD_MB}MB."
        )

    # Save to disk with unique filename to prevent path traversal
    safe_filename = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    with open(file_path, "wb") as f:
        f.write(contents)

    # Extract text
    try:
        extracted_text = extract_text_from_file(file_path, ext).strip()
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to parse document text: {str(e)}"
        )

    if not extracted_text:
        raise HTTPException(status_code=400, detail="The uploaded file contains no readable text.")

    # Split into chunks of ~1200 chars if large
    chunks = []
    chunk_size = 1200
    if len(extracted_text) <= chunk_size:
        chunks.append(extracted_text)
    else:
        start = 0
        while start < len(extracted_text):
            chunk = extracted_text[start:start + chunk_size].strip()
            if chunk:
                chunks.append(chunk)
            start += chunk_size - 150  # 150 char overlap

    base_title = title or os.path.splitext(filename)[0]
    created_entries = []

    for idx, chunk in enumerate(chunks, 1):
        chunk_title = f"{base_title} (Part {idx}/{len(chunks)})" if len(chunks) > 1 else base_title
        entry = KnowledgeEntry(
            id=str(uuid.uuid4()),
            knowledge_id=f"DOC-{str(uuid.uuid4())[:8].upper()}",
            title=chunk_title,
            content=chunk,
            retrieval_text=f"{chunk_title}\n{chunk}",
            record_type=record_type,
            category=category,
            source_type="upload",
            source_filename=filename,
            source_quality="official",
            data_status="verified",
            indexing_status="indexed"
        )
        db.add(entry)
        created_entries.append(entry)

    db.commit()

    # Synchronize index
    reload_retriever_from_db(db)

    return {
        "status": "success",
        "message": f"Successfully indexed {len(created_entries)} chunks from '{filename}'.",
        "filename": filename,
        "chunks_indexed": len(created_entries),
    }


@router.post("/seed", response_model=Dict[str, Any])
def reseed_knowledge_base(
    force: bool = False,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Reseed or refresh dataset entries from the project CSVs."""
    seed_knowledge_from_csv(db, force=force)
    count = db.query(KnowledgeEntry).count()
    return {
        "status": "success",
        "total_entries": count,
        "message": "Knowledge base seeded and vector index refreshed successfully."
    }
