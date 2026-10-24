# Maharashtra OBC Education Voice AI Chatbot
## Next-Generation Local AI Application

This is a professional redesign and architectural overhaul of the Maharashtra OBC Education Chatbot. It leverages local LLMs via Ollama and a robust RAG pipeline to provide grounded, multilingual information about education schemes for OBC students.

## 🚀 Project Structure

```text
new-obc-ai-app/
├── frontend/           # React + Vite + Tailwind CSS
├── backend/            # FastAPI Application
│   ├── app/
│   │   ├── api/        # Route handlers
│   │   ├── core/       # Config, Security, Constants
│   │   ├── models/     # SQLAlchemy Database Models
│   │   ├── repositories/ # Data Access Layer
│   │   ├── schemas/    # Pydantic Validation Schemas
│   │   └── services/   # Business Logic (AI, RAG, Storage)
│   └── requirements.txt
├── data/               # Data Lake
│   ├── raw/            # Original CSVs
│   ├── processed/      # Cleaned/Normalized data
│   └── evaluation/     # Benchmarks and test sets
├── storage/            # Persistence
│   ├── chroma_db/      # Vector Store
│   └── obc_chatbot.db  # SQLite Database
├── scripts/             # Maintenance and Ingestion scripts
└── docs/               # Technical documentation
```

## 🛠️ Technology Stack

- **Frontend**: React 18, Vite, Tailwind CSS, Lucide React, Framer Motion.
- **Backend**: FastAPI, Python 3.12, SQLAlchemy.
- **AI Engine**: Ollama (Llama 3.2 / Qwen 2.5).
- **Vector Store**: ChromaDB.
- **Embeddings**: Multilingual MiniLM-L12-v2.
- **Database**: SQLite.

## 🏁 Setup Instructions (Windows)

### 1. AI Runtime
- Install [Ollama](https://ollama.com/).
- Pull the required model:
  ```powershell
  ollama pull llama3.2
  ```

### 2. Backend Setup
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
uvicorn app.main:app --reload
```

### 3. Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```
