# Voice AI Chatbot

A student-friendly, full-stack voice chatbot project with text chat,
voice-to-text, text-to-speech, voice-to-voice conversation, user
accounts, chat history, and a knowledge base with retrieval-augmented
generation (RAG).

The initial implementation is designed to be affordable: use a free-tier
text-generation API where available, browser speech capabilities for the
first prototype, and local multilingual embeddings for document search.
Free-tier quotas, model names, and API terms can change; verify current
provider documentation before deploying.

## 1. Project goals

Build a working application that supports:

-   **Text chat:** users type a message and receive an AI-generated
    answer.
-   **Voice-to-text (STT):** users speak and see an editable transcript.
-   **Text-to-speech (TTS):** users can listen to an AI answer.
-   **Voice-to-voice:** users speak, the system transcribes the request,
    generates an answer, and plays it aloud.
-   **Multilingual conversation:** support Hindi, English, Marathi, Gujarati,
    Tamil, Telugu, Bengali, and any additional languages supported and tested
    by the selected AI and speech engines. Include Auto-detect and manual
    language selection, language-matched responses, and voice playback.
-   **Mixed-language conversation:** support common code-switching such as
    Hinglish where the chosen speech-recognition engine can recognize it.
-   **Conversation history:** save and reload prior chats.
-   **Knowledge base:** administrators can add, view, search, edit, and
    delete knowledge records and upload documents.
-   **RAG:** answers can use relevant retrieved knowledge rather than
    relying only on the model's general knowledge.
-   **Automatic knowledge synchronization:** new, edited, or deleted
    knowledge is reflected in future retrievals without manually
    rebuilding the entire application.
-   **Admin and student roles:** administrators manage knowledge;
    students ask questions and view their own history.
-   **Security:** backend-only API keys, password hashing, role checks,
    validation, and safe upload handling.

## Implementation Status & Quickstart

> **Status: FULLY ENHANCED WITH LOCAL OPEN-WEIGHT LLM RUNTIME (Zero Paid API Keys Required).**
>
> 100% locally runnable AI chatbot powered by **Ollama** running **Llama 3.2 (3.2B parameters, Q4_K_M GGUF)** on local CPU/RAM. Zero exposed API keys, zero paid cloud subscriptions.
> Includes 10+ Indic languages + Hinglish/Gujlish code-switching, full-featured per-message audio controls (Listen/Pause/Resume, Replay, Stop, Equalizer), global interruption controls, light/dark theme system, non-blocking toasts, Indic typography, real-time generation metrics (latency, tokens, tokens/sec, $0.00 cost), sanitized knowledge sources, model runtime monitor modal, and robust error handling.

### Quickstart (Local Windows Setup)

1. **Install Ollama & Download Model (Zero API Key Needed)**:
   - Install Ollama for Windows via installer from [ollama.com](https://ollama.com/download) or terminal:
     ```powershell
     winget install Ollama.Ollama
     ```
   - Download and verify the local open-weight model:
     ```powershell
     ollama pull llama3.2:latest
     ```
   - Ensure the Ollama runtime is running (starts automatically, or run):
     ```powershell
     ollama serve
     ```

2. **Backend Setup & Dependencies**:
   ```powershell
   python -m pip install -r requirements.txt
   ```

3. **Configuration**:
   Copy `.env.example` to `.env` (configured for Ollama by default):
   ```env
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.2:latest
   OLLAMA_TIMEOUT=120.0
   ```

4. **Start the Application**:
   ```powershell
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
   ```

5. **Access the Application**:
   - Web App UI: `http://127.0.0.1:8000/`
   - Model Runtime Status: Click the **Ollama (llama3.2)** status pill in the top navigation bar.
   - Interactive Swagger API Documentation: `http://127.0.0.1:8000/docs`
   - LLM Health Status API: `http://127.0.0.1:8000/api/llm/status`
   - Health Check: `http://127.0.0.1:8000/health`

### Default User Credentials
- **Administrator**: `admin` / `Admin@123` (Access to Knowledge Base Management, Document Uploads, Benchmark Suite)
- **Student**: `student` / `Student@123` (Or register any new student account via UI)

### Automated Test Suite
Run the test suite verifying Ollama integration and conversation pipeline:
```powershell
python -m pytest tests/test_ollama.py -v
python -m pytest tests/ -v
```

### Key Capabilities Implemented
- **Expanded Multilingual Support (10+ Languages & Code-Switching)**:
  - English (`en`), Hindi (`hi`), Marathi (`mr`), Gujarati (`gu`), Tamil (`ta`), Telugu (`te`), Bengali (`bn`), Kannada (`kn`), Malayalam (`ml`), Punjabi (`pa`).
  - Code-Switching modes: Hinglish (`hinglish` - Hindi in Latin script) and Gujlish (`gujlish` - Gujarati in Latin script).
  - High-precision automatic language detection via Unicode script range analysis and lexical frequency scoring.
- **Upgraded Speech & Voice Pipeline**:
  - Full Web Speech STT and TTS pipeline for all 10+ supported locales.
  - Multi-state per-message audio player: **Listen / Pause / Resume**, **Stop**, **Replay**, and animated 4-bar **Equalizer**.
  - **Global Speaking Bar**: Top indicator displaying language, live equalizer wave, and one-click global Pause/Stop buttons to interrupt audio anytime.
  - **Strict Language Consistency Protection**: If native TTS voice for an Indian language is not installed on the user's OS/browser, the app prevents discordant English voice playback and notifies the user with a non-blocking toast.
  - Error-resilient STT handling microphone permission denials (`not-allowed`), silence (`no-speech`), and network interruptions.
- **Professional UI/UX Redesign**:
  - Light / Dark theme toggle persisted in `localStorage` with cohesive color tokens.
  - Native Google Fonts linked for all major Indian scripts (`Noto Sans Devanagari`, `Gujarati`, `Tamil`, `Telugu`, `Bengali`, `Kannada`, `Malayalam`, `Gurmukhi`).
  - Non-blocking toast notification system replacing intrusive browser `alert()` popups.
  - Verified source references rendered with distinct tags and verified portal links (MahaDBT, myScheme, MAHAJYOTI, OBC Bahujan Kalyan).
- **GenAI Evaluation & Performance Metrics**:
  - Per-message metrics badge showing generation latency (ms), input/output token estimates, and estimated request cost.
  - Built-in GenAI Evaluation Suite with automated benchmarks, RAG ablation comparisons, parameter sweep experiments, and exportable CSV/JSON reports.
- **Sanitized Knowledge Base**:
  - Over 118 verified educational scheme records pre-indexed and cleanly parsed.
- **Security & Privacy**:
  - Bcrypt password hashing, JWT bearer auth, user-isolated chat history, role-based protection, and zero external API dependencies.

---

## 2. Suggested technology stack

  ------------------------------------------------------------------------
  Layer                   Recommended choice       Notes
  ----------------------- ------------------------ -----------------------
  Frontend                HTML, CSS, vanilla       Simple starting point
                          JavaScript               that matches the
                                                   supplied folder
                                                   structure

  Backend                 Python 3.11 or 3.12 +    Avoid dependency
                          FastAPI                  surprises by using a
                                                   supported Python
                                                   version

  API server              Uvicorn                  Runs the FastAPI
                                                   application

  AI text generation      Ollama (Llama 3.2 3B /   100% local open-weight
                          Qwen 2.5 3B local GGUF)  inference; zero API keys,
                                                   zero cost ($0.00)

  Speech-to-text          Browser Web Speech API   Browser support and
                          initially; local         network behavior vary
                          Whisper/faster-whisper   
                          as an alternative        

  Text-to-speech          Browser SpeechSynthesis  Available voices vary
                          initially; a local TTS   by operating system and
                          engine as an alternative browser

  Database                SQLite for the first     Upgrade to
                          version                  MySQL/PostgreSQL if
                                                   needed

  Database ORM            SQLAlchemy               Models and database
                                                   access

  Authentication          Password hashing +       Never store plaintext
                          signed session/JWT       passwords
                          approach                 

  Document parsing        pypdf, python-docx,      PDF, DOCX, CSV, XLSX,
                          pandas, openpyxl         and TXT support

  RAG vector search       ChromaDB or FAISS        Persist the index and
                                                   track source record IDs

  Embeddings              Multilingual             Choose a model that
                          sentence-transformers    supports both English
                          model                    and Hindi

  Testing                 pytest + FastAPI         Test APIs and critical
                          TestClient               workflows
  ------------------------------------------------------------------------

Start with browser speech features and SQLite. Add local transcription,
neural speech, and more advanced streaming only after the end-to-end MVP
works.

## 3. Folder structure

Create this structure from the project root:

``` text
voice-ai-chatbot/
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   ├── speech.py
│   │   ├── auth.py
│   │   └── knowledge.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py
│   │   ├── stt_service.py
│   │   ├── tts_service.py
│   │   └── retrieval_service.py
│   ├── database.py
│   └── models.py
├── knowledge/
│   └── uploads/
├── tests/
│   ├── test_health.py
│   ├── test_chat.py
│   └── test_knowledge.py
├── .env
├── .env.example
├── .gitignore
└── requirements.txt
```

Keep uploaded documents and generated indexes out of source control.
Create directories automatically in application startup if they do not
exist.

## 4. Windows setup (VS Code)

### Prerequisites

1.  Install Python 3.11 or 3.12.
2.  Install VS Code.
3.  Open the project folder in VS Code.
4.  Open the integrated terminal.

### Create and activate a virtual environment

PowerShell:

``` powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
```

If PowerShell blocks activation, use Command Prompt and run:

``` bat
.venv\Scripts\activate.bat
```

### Install dependencies

Create `requirements.txt` with the initial dependencies:

``` text
fastapi
uvicorn[standard]
python-dotenv
pydantic
sqlalchemy
passlib[bcrypt]
python-jose[cryptography]
python-multipart
pypdf
python-docx
pandas
openpyxl
chromadb
sentence-transformers
pytest
httpx
```

Install them:

``` powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Some ML packages are large and may take time to install. If installation
fails, read the first package error and check its supported Python
versions rather than installing random package versions.

## 5. Environment variables

Copy `.env.example` to `.env` and fill in your own values. Never commit
`.env`.

Example `.env.example`:

``` dotenv
APP_NAME=Voice AI Chatbot
APP_ENV=development
SECRET_KEY=replace-with-a-long-random-secret
DATABASE_URL=sqlite:///./voice_chatbot.db

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest
OLLAMA_TIMEOUT=45.0

UPLOAD_DIR=knowledge/uploads
MAX_UPLOAD_MB=15

# Optional: use a provider or local engine if browser speech is not sufficient.
STT_PROVIDER=browser
TTS_PROVIDER=browser
```

Generate a secret key locally, for example:

``` powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Paste the output into your private `.env` file. Keep `.env.example` free of real credentials. Core inference is local-only;
the application does not fall back to a cloud LLM when Ollama is unavailable.

## 6. Application implementation phases

### Phase A --- Health endpoint and server

1.  Implement `backend/main.py` with a FastAPI app.
2.  Add a `GET /health` endpoint returning `{"status": "ok"}`.
3.  Mount routers from `backend/routes/`.
4.  Configure CORS for the exact local frontend origin during
    development.
5.  Run the server from the project root:

``` powershell
uvicorn backend.main:app --reload
```

Open `http://127.0.0.1:8000/health` and `http://127.0.0.1:8000/docs`.

**Done when:** the health endpoint returns success and the API docs
load.

### Phase B --- Text chat and AI provider

Implement `backend/services/ai_service.py` as the only module that talks
to the model provider. It should:

-   Read provider credentials from environment variables.
-   Validate that a message is not empty and enforce a sensible length
    limit.
-   Use a configurable model name rather than scattering model names
    across the code.
-   Catch provider errors and return safe, useful errors to the API
    layer.
-   Never log API keys or sensitive conversation content unnecessarily.
-   Support a system instruction that tells the model to be honest when
    it cannot find an answer in provided college knowledge.

Implement `POST /api/chat` to accept JSON similar to:

``` json
{
  "message": "When does the library close?",
  "conversation_id": null,
  "language": "en"
}
```

Return a consistent response:

``` json
{
  "answer": "The library closing time is ...",
  "conversation_id": "server-generated-id",
  "sources": []
}
```

The examples above define the intended contract; generate conversation
IDs on the server and validate all inputs. Do not expose provider
credentials to the browser.

**Done when:** a typed message reaches the backend, the AI provider is
called, and the answer appears in the UI.

### Phase C --- Frontend chat

In `frontend/index.html`, add:

-   A message list.
-   A text input and Send button.
-   A microphone button.
-   A language selector for English and Hindi.
-   A speaker button on assistant messages.
-   A conversation-history area.
-   Clear loading, error, recording, and playback states.

In `frontend/app.js`:

-   Send requests to the backend using `fetch`.
-   Render user and assistant messages as text, not unsanitized HTML.
-   Disable duplicate submissions while a request is pending.
-   Handle failed requests and empty messages.
-   Keep the API base URL in one configuration constant.
-   Do not put API keys in frontend JavaScript.

Serve the frontend from FastAPI or use a local development server.
Configure CORS to match the actual frontend origin. Microphone APIs
generally require HTTPS or localhost.

**Done when:** text chat works in a browser and the page does not lose
the conversation currently being displayed during normal interactions.

### Phase D --- Voice-to-text (STT)

Implement `backend/services/stt_service.py` behind a simple interface so
the speech provider can be changed later.

For the first prototype, browser speech recognition can populate the
text field directly. In browsers that support it, set the recognition
language to `en-IN` for English or `hi-IN` for Hindi. These locale
choices do not guarantee support or accurate recognition in every
browser.

For a backend STT option:

1.  Record audio in the browser.
2.  Send it as multipart form data to `POST /api/speech/transcribe`.
3.  Validate file type, file size, and duration.
4.  Transcribe using the selected speech engine.
5.  Return a transcript and detected/selected language.
6.  Let the user edit the transcript before sending it to chat.

Handle microphone permission denial, unsupported browsers, silence,
network errors, and empty transcripts.

**Done when:** a user can speak a phrase, see the transcript, correct
it, and send it as a normal chat message.

### Phase E --- Text-to-speech (TTS)

Implement `backend/services/tts_service.py` with a provider-neutral
interface.

For the first version, use browser `speechSynthesis`:

-   Select a suitable available English or Hindi voice.
-   Display Play and Stop controls.
-   Cancel prior speech before starting new speech.
-   Handle missing voices and unsupported languages.
-   Do not assume the same voice list exists on every device.

If using server-side TTS later, implement `POST /api/speech/synthesize`,
return an appropriate audio content type, and avoid exposing public URLs
to private audio files.

**Done when:** an assistant answer can be read aloud and stopped by the
user.

### Phase F --- Voice-to-voice

For a reliable first version, use a turn-based pipeline:

1.  User presses the microphone button.
2.  The browser records one utterance.
3.  Speech recognition produces text.
4.  The transcript is shown to the user.
5.  The transcript is sent to the chat endpoint.
6.  The assistant answer is displayed.
7.  Text-to-speech reads the answer aloud.
8.  The user can stop playback or start another turn.

Add hands-free mode only after this flow works. Use explicit state such
as `idle`, `recording`, `processing`, and `speaking`; prevent
overlapping recordings, duplicate requests, and audio playback. Always
provide a way to interrupt speech.

**Done when:** a user can ask a question aloud and hear the answer
without typing.

### Phase G --- Database and authentication

Use SQLAlchemy models for:

-   `User`: id, email/username, password hash, role, created timestamp.
-   `Conversation`: id, owner user id, title, created/updated
    timestamps.
-   `Message`: id, conversation id, role, text, timestamp.
-   `KnowledgeEntry`: id, title, content, source type, source filename
    if applicable, updated timestamp, and indexing status.

Implement password hashing, login, logout/token handling, and
server-side role checks. An administrator must be created through a safe
setup process; do not allow public registration to select the admin
role.

Every conversation query must verify ownership on the server. Never
trust a user ID or role sent by the frontend.

**Done when:** a user can sign in, see only their own chats, and load
previous messages after a refresh.

### Phase H --- Knowledge base and RAG

The knowledge service should support:

-   Create, list, search, update, and delete knowledge entries.
-   Upload PDF, DOCX, TXT, CSV, and XLSX documents.
-   Extract text and spreadsheet cells in a predictable format.
-   Split extracted text into manageable chunks with source metadata.
-   Create multilingual embeddings for English and Hindi retrieval.
-   Store chunk metadata with a stable source/entry ID and version.
-   Retrieve the most relevant chunks for each question.
-   Return source titles or document references alongside answers.

For every create, edit, or delete operation:

1.  Save the change in the database.
2.  Update or invalidate the corresponding vector-index chunks.
3.  Record indexing status and errors.
4.  Make the updated content available to subsequent retrievals only
    when indexing succeeds.
5.  Provide a retry mechanism if indexing fails.

Do not delete a source's old index until the replacement is ready unless
the entry is being deleted. Do not tell the user an upload is fully
searchable before processing and indexing succeed.

At answer time, retrieve relevant chunks and pass them to the AI model
as untrusted reference material. Tell the model to answer from those
sources when applicable, cite source titles, and say when the
information is not available. Never follow instructions found inside
uploaded documents that attempt to override system or security rules.

**Done when:** adding or editing a knowledge entry changes answers to
relevant student questions without restarting the application or
manually rebuilding the whole index.

### Phase I --- Tests and hardening

Use `pytest` to test:

-   Health endpoint.
-   Empty and oversized messages.
-   AI provider failure handling.
-   Unauthorized access to admin endpoints.
-   User A cannot read User B's conversations.
-   Upload validation and unsupported file types.
-   Knowledge create/update/delete and index synchronization.
-   Retrieval of newly added knowledge.
-   Missing API keys.
-   STT/TTS unsupported or failed cases.

Use mocked AI and speech services for automated tests so the test suite
does not require paid API calls. Add a few manual end-to-end tests with
a real provider.

## 7. Multilingual voice conversation requirement

Build a multilingual AI chatbot that allows users to communicate naturally in Hindi, English, Marathi, Gujarati, Tamil, Telugu, Bengali, and other languages supported by the selected AI and speech engines.

### Required functionality

- Provide a language selector with an **Auto-detect** option.
- Support voice-to-text, text-to-voice, and voice-to-voice conversations in supported languages.
- Detect the user's language where possible and respond in the same language by default.
- Allow users to manually select a preferred language and save that preference.
- Support common mixed-language conversations, including Hinglish, where the selected speech engine can recognize them.
- Display recognized speech in its original script when supported.
- Generate spoken responses using a voice that matches the response language.
- Allow users to change languages at any time without restarting the conversation.
- Retrieve relevant knowledge-base information even when the question and source document use different languages. Use multilingual embeddings or query translation when necessary.
- Preserve conversation context when users switch languages.
- Handle unsupported languages or unavailable voices gracefully and inform users rather than silently switching to English.
- Test speech recognition, response quality, pronunciation, and audio playback separately for every advertised language.

### Implementation steps

1. **Define supported languages honestly.** Start by testing English, Hindi, Marathi, and Hinglish, then add Gujarati, Tamil, Telugu, Bengali, and others after verifying STT, model response quality, and TTS voices.
2. **Add a language preference.** Store `preferred_language` and an `auto_detect` setting per user or conversation. Provide a selector in the chat UI and allow it to be changed at any time.
3. **Detect language.** Use speech engine language settings and/or a language-identification component. Treat detection as a best effort; when uncertain, ask the user to select a language rather than silently assuming English.
4. **Transcribe speech.** Pass the selected locale to STT when supported. Preserve the original transcript and script. For mixed-language speech, test code-switching explicitly because some engines handle it better than others.
5. **Instruct the AI model.** Send a system instruction that requests an answer in the selected language; in Auto-detect mode, use the detected language. Preserve conversation context when the user switches languages. Do not translate proper names or technical terms unnecessarily.
6. **Connect multilingual RAG.** Prefer a multilingual embedding model, such as `paraphrase-multilingual-MiniLM-L12-v2`, and test retrieval with questions in a different language from the source document. If retrieval quality is inadequate, add query translation as a fallback and retain the original question for context.
7. **Select a matching TTS voice.** Map each supported language to an available speech voice. Check available voices at runtime; if none is available, show a clear message and keep the answer readable instead of pretending audio was generated.
8. **Test each language separately.** Create test prompts for transcription, spelling/script, answer relevance, pronunciation, voice availability, switching languages, and mixed-language messages. Do not advertise a language as fully supported until it passes these checks.

**Acceptance criteria:** A user can ask a question in Hindi or another supported language, receive a relevant answer in that language, and hear the answer spoken aloud without needing to communicate in English.

> Browser STT/TTS support and voice quality vary by browser, device, operating system, and locale. Language support must be verified in the actual target environment; a language selector alone does not guarantee working speech recognition or natural speech output.

## 8. AI engineer workflow: build, evaluate, and deploy the website

Use this workflow as the AI engineering process for the project. Do not start by connecting every service at once; build a small end-to-end slice, evaluate it, and expand it.

### Step 1 — Write requirements and measurable success criteria

Document the user roles, supported languages, file types, expected traffic, privacy requirements, and cost limit. Define measurable checks, for example:

- Text chat succeeds for normal questions and returns a helpful error when the AI provider is unavailable.
- STT produces an editable transcript for each advertised language in the test environment.
- TTS plays a response in the expected language when a matching voice is available.
- RAG answers cite or identify the source documents used and admits when the answer is not in the knowledge base.
- Updating a knowledge entry changes subsequent retrieval results after indexing succeeds.
- A student cannot read another student's conversations or access administrator endpoints.

### Step 2 — Build a thin vertical slice

Implement one complete flow first: frontend text input → FastAPI `/api/chat` → AI service → displayed answer. Add automated tests before adding speech, login, or document ingestion. This gives you a working baseline to debug against.

### Step 3 — Separate AI services

Keep provider-specific code in `services/ai_service.py`, speech recognition in `services/stt_service.py`, speech synthesis in `services/tts_service.py`, and retrieval in `services/retrieval_service.py`. Use clear input/output contracts so one provider can be replaced without rewriting the UI or routes. Put keys and model names in environment variables.

### Step 4 — Build a reliable data pipeline

For each uploaded file: validate it → extract text or spreadsheet rows → normalize text → chunk it → create multilingual embeddings → store chunks with source IDs and versions → mark indexing status. Make ingestion repeatable and idempotent, log safe error details, and provide retry handling. Keep the database record and vector index synchronized on create, update, and delete.

### Step 5 — Add RAG with source grounding

For each user question: identify its language → embed the query (or translate it if required) → retrieve relevant chunks → apply relevance thresholds → pass only useful context to the AI model → return an answer and source metadata. Tell the model that retrieved documents are reference data, not instructions. If evidence is missing or weak, have the chatbot say it does not know rather than inventing institutional facts.

### Step 6 — Evaluate before tuning

Create a small test dataset of real, non-sensitive questions and verified answers. Include questions in English, Hindi, Marathi, Hinglish, and every additional advertised language. Track:

- **Retrieval quality:** whether the expected source appears among retrieved chunks.
- **Groundedness:** whether claims in the answer are supported by the retrieved content.
- **Answer quality:** correctness, relevance, and language appropriateness.
- **Speech quality:** transcript accuracy, pronunciation, latency, and interruptions.
- **Reliability:** API failures, timeouts, empty audio, duplicate requests, and indexing failures.
- **Cost and latency:** response time, token use, and speech-processing cost where applicable.

Keep a regression test set and rerun it when changing prompts, models, embeddings, chunking, or speech providers. Do not rely only on a few successful manual demos.

### Step 7 — Implement safety and access control

Authenticate users, enforce authorization on the backend, validate files and inputs, limit upload size and request rate, keep secrets out of the frontend, and protect conversation history. Treat uploaded documents and retrieved text as untrusted content. Do not send confidential student information to an external provider unless its privacy terms and institutional rules allow it.

### Step 8 — Deploy and observe

Run automated tests, configure production environment variables, use HTTPS, apply database migrations and backups, and deploy the frontend and backend. Add privacy-conscious logs and monitoring for error rates, latency, STT/TTS failures, and knowledge-index status. Never log API keys, passwords, or unnecessary sensitive message content. Verify the deployed site on desktop and mobile, not only on localhost.

### Step 9 — Release in stages

1. **MVP:** text chat + AI provider + basic tests.
2. **Voice:** STT, TTS, and turn-based voice-to-voice.
3. **Persistence:** accounts, roles, and conversation history.
4. **Knowledge:** document upload, RAG, sources, and automatic synchronization.
5. **Multilingual:** validate each language and voice, then expand coverage.
6. **Production:** security review, deployment, monitoring, backups, and regression tests.

**AI engineering definition of done:** the app is not complete merely because it calls an AI API. It must have repeatable data processing, evaluated retrieval and answers, graceful failure handling, security controls, tests, deployment instructions, and verified language support.

## 9. API endpoint plan

  ---------------------------------------------------------------------------------
  Method            Endpoint                    Purpose           Access
  ----------------- --------------------------- ----------------- -----------------
  `GET`             `/health`                   Health check      Public

  `POST`            `/api/auth/register`        Register a        Public
                                                student account   

  `POST`            `/api/auth/login`           Sign in           Public

  `POST`            `/api/chat`                 Generate an       Authenticated
                                                answer using chat 
                                                history and RAG   

  `GET`             `/api/conversations`        List current      Authenticated
                                                user's            
                                                conversations     

  `GET`             `/api/conversations/{id}`   Load a            Owner only
                                                conversation      
                                                owned by the user 

  `POST`            `/api/speech/transcribe`    Transcribe        Authenticated
                                                uploaded audio if 
                                                server-side STT   
                                                is enabled        

  `POST`            `/api/speech/synthesize`    Generate audio if Authenticated
                                                server-side TTS   
                                                is enabled        

  `GET`             `/api/knowledge`            Search/list       Admin; expose
                                                knowledge entries only approved
                                                                  content to
                                                                  students if
                                                                  needed

  `POST`            `/api/knowledge`            Create a          Admin
                                                knowledge entry   

  `POST`            `/api/knowledge/upload`     Upload and index  Admin
                                                a document        

  `PUT`             `/api/knowledge/{id}`       Edit a knowledge  Admin
                                                entry             

  `DELETE`          `/api/knowledge/{id}`       Delete a          Admin
                                                knowledge entry   
                                                and invalidate    
                                                its chunks        
  ---------------------------------------------------------------------------------

The API contract can evolve, but keep endpoint behavior consistent and
document any changes.

## 10. Security checklist

-   [ ] Keep secrets in `.env`, never in frontend code or Git.
-   [ ] Use password hashing; never store plaintext passwords.
-   [ ] Enforce role checks on every admin route.
-   [ ] Enforce conversation ownership on every history route.
-   [ ] Validate input lengths, upload sizes, and accepted file types.
-   [ ] Generate stored filenames on the server; do not trust upload
    paths.
-   [ ] Configure CORS for known frontend origins.
-   [ ] Use HTTPS in production.
-   [ ] Rate-limit authentication and expensive AI endpoints.
-   [ ] Avoid logging API keys, passwords, and unnecessary private
    content.
-   [ ] Review AI provider data retention, privacy terms, quotas, and
    pricing before sending real student data.
-   [ ] Treat uploaded documents and retrieved text as untrusted
    content.
-   [ ] Back up the database and knowledge files before upgrades or
    migrations.

## 11. Common problems

**`ModuleNotFoundError`**\
Activate the virtual environment and run
`pip install -r requirements.txt` using the same Python interpreter that
runs Uvicorn.

**AI API key missing or rejected**\
Check `.env`, ensure the app loads it from the project root, verify that
the key is valid, and check provider quota and model availability.
Restart the backend after changing environment variables.

**CORS error**\
Use the exact frontend origin in the backend CORS configuration. A
different port is a different origin.

**Microphone does not work**\
Grant browser permission and use `localhost` or HTTPS. Check browser
support and whether another application is using the microphone.

**Hindi voice is missing**\
The device may not have a suitable voice installed. Test another
supported browser/device or configure a speech engine that provides a
Hindi voice.

**New knowledge is not reflected in answers**\
Check extraction errors, chunk creation, embedding/index status, source
IDs, and retrieval results. Confirm the answer request calls the
retrieval service and that stale chunks are invalidated.

**Slow first request**\
Local embedding or speech models may download model files or initialize
on first use. Large documents and free-tier API rate limits can also
increase latency.

## 12. Run and verify

From the project root, activate the virtual environment and run:

``` powershell
uvicorn backend.main:app --reload
```

Then:

1.  Open `http://127.0.0.1:8000/health`.
2.  Open `http://127.0.0.1:8000/docs`.
3.  Test text chat.
4.  Open the frontend on localhost.
5.  Test microphone permission and voice-to-text.
6.  Test speaking an AI response.
7.  Test a complete voice-to-voice turn.
8.  Sign in as an administrator and add a knowledge entry.
9.  Ask a question that requires that entry.
10. Edit and delete the entry and verify subsequent retrieval behavior.
11. Sign in as a student and confirm that admin functions are
    inaccessible.
12. Run `pytest` from the project root.

## 13. Definition of done

The project is ready for a first usable release only when:

-   Text chat works end to end.
-   Voice-to-text, text-to-speech, and voice-to-voice work in the
    supported test environment.
-   Every advertised language has been tested on the intended browser/device, including transcription, answer language, pronunciation, voice availability, and language switching.
-   Conversations persist in the database and remain private to their
    owner.
-   Admin and student permissions are enforced by the backend.
-   Knowledge CRUD and document uploads work.
-   New and edited knowledge is reflected in retrieval after successful
    indexing.
-   Errors are handled without crashing the app or exposing secrets.
-   The setup instructions have been followed successfully on a clean
    environment.
-   Automated tests pass and the critical workflows have been manually
    verified.

## 14. Helpful official documentation

-   FastAPI: https://fastapi.tiangolo.com/
-   Uvicorn: https://www.uvicorn.org/
-   Gemini API: https://ai.google.dev/gemini-api/docs
-   Python `venv`: https://docs.python.org/3/library/venv.html
-   SQLAlchemy: https://docs.sqlalchemy.org/
-   Chroma: https://docs.trychroma.com/
-   Sentence Transformers: https://www.sbert.net/
-   MDN Web Speech API:
    https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API
-   pytest: https://docs.pytest.org/

------------------------------------------------------------------------

**Build strategy:** finish one phase, test it, and only then continue.
The most important milestone is a complete text-chat path first; speech,
history, RAG, and role-based dashboards can then be added without
debugging the entire system at once.
