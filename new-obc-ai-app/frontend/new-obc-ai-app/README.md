# 🎓 Maharashtra OBC Education Voice AI Chatbot

A professional, RAG-powered, multilingual voice assistant designed to provide grounded information about educational schemes, scholarships, and hostel guidelines for OBC students in Maharashtra.

## 🌟 Key Features

- **Local LLM Inference**: Powered by **Ollama (Llama 3.2)**. No external API keys required, ensuring 100% privacy and zero cost.
- **Multilingual Voice-to-Voice**: Full support for English, Hindi, and Marathi using a seamless STT $\rightarrow$ LLM $\rightarrow$ TTS pipeline.
- **Grounded RAG**: Uses **ChromaDB** and multilingual embeddings to ensure answers are derived from official government records, preventing AI hallucinations.
- **Professional SaaS UI**: A modern, responsive React frontend featuring a high-conversion landing page and a polished chat dashboard.
- **Source Transparency**: Every AI response includes clickable citations to the specific government record used for the answer.

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React 18, Vite, Tailwind CSS | Professional, responsive UI/UX |
| **Backend** | FastAPI (Python 3.12) | High-performance asynchronous API |
| **AI Engine** | Ollama (Llama 3.2) | Local open-weight LLM inference |
| **Vector Store** | ChromaDB | Efficient retrieval of scheme documents |
| **Embeddings** | Multilingual MiniLM-L12-v2 | Cross-lingual semantic search |
| **Database** | SQLite | Persistent storage for user and chat data |

---

## 🚀 Installation & Setup (Windows)

### 1. Install AI Runtime
1. Download and install **Ollama** from [ollama.com](https://ollama.com/).
2. Open PowerShell and pull the model:
   ```powershell
   ollama pull llama3.2
   ```
3. Ensure Ollama is running in the background.

### 2. Backend Setup
```powershell
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env to set OLLAMA_BASE_URL=http://localhost:11434

# Start the server
uvicorn app.main:app --reload
```

### 3. Data Ingestion (Crucial Step)
To populate the AI's knowledge base from the provided datasets:
```powershell
# Run from the project root
python scripts/ingest_data.py
```
*This will process the CSVs in `data/raw/` and create the vector index in `storage/chroma_db`.*

### 4. Frontend Setup
```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
Access the app at: `http://localhost:5173`

---

## 📖 Project Architecture

### Data Flow
`User Voice/Text` $\rightarrow$ `FastAPI` $\rightarrow$ `ChromaDB (Context Retrieval)` $\rightarrow$ `Ollama (Grounded Generation)` $\rightarrow$ `FastAPI` $\rightarrow$ `Frontend (Text + Speech)`

### Folder Structure
- `backend/app/services`: Contains the core logic for Ollama, Retrieval, and Ingestion.
- `backend/app/api`: Defines the REST endpoints.
- `frontend/src/pages`: Contains the Landing and Chat pages.
- `data/raw`: Stores the original government datasets.
- `storage`: Holds the SQLite DB and ChromaDB vector index.

---

## 🛠️ Maintenance & Troubleshooting

### Common Issues
- **Ollama Connection Error**: Ensure Ollama is running. Check `http://localhost:11434` in your browser.
- **Voice Not Working**: Ensure you are using a modern browser (Chrome/Edge) and have granted microphone permissions.
- **Incorrect Answers**: Run `python scripts/ingest_data.py` again to ensure the vector store is up-to-date.

### Adding New Data
1. Place new CSV files in `data/raw/`.
2. Update the `csv_mapping` in `scripts/ingest_data.py` to include the new file and its text columns.
3. Run the ingestion script.

---

## ⚖️ Privacy & Security
This application is designed for **Local-First AI**. No data is sent to cloud providers like OpenAI or Google. All processing happens on the user's local hardware via Ollama and ChromaDB.
