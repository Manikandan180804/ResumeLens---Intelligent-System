# 🧠 ResumeIntelligence AI

**Multi-Agent Resume Intelligence and Candidate Evaluation System**

A sophisticated AI system powered by **LangGraph orchestration**, **FAISS vector database**, and **sentence-transformers** that evaluates resumes against job descriptions with deep semantic understanding.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     LangGraph Agent Workflow                         │
│                                                                       │
│  📄 Resume Parser → 💼 JD Analyzer → 🔢 Embedder → 🔍 Semantic     │
│       ↓                   ↓               ↓             Matcher      │
│  (Skills, Exp)     (Requirements)   (FAISS Store)          ↓         │
│                                                      🧩 Skill Gap    │
│                                                      Analyzer        │
│                                                           ↓          │
│                                                      📊 Scorer       │
│                                                           ↓          │
│                                                      💡 Recommender  │
│                                                           ↓          │
│                                                      🏆 Ranker       │
│                                                           ↓          │
│                                                      📈 Analytics    │
│                                                           ↓          │
│                                                      💾 DB Persist   │
└─────────────────────────────────────────────────────────────────────┘
         │                                         │
    FastAPI Backend                         SQLite Database
    (Port 8000)                         (resume_intelligence.db)
         │
    Streamlit UI
    (Port 8501)
```

## 🤖 The 9 AI Agents

| # | Agent | Role |
|---|-------|------|
| 1 | **Resume Parser** | Extracts name, email, skills, experience, education |
| 2 | **JD Analyzer** | Identifies required/preferred skills & requirements |
| 3 | **Embedding Agent** | Generates 384-dim vectors via sentence-transformers |
| 4 | **Semantic Matcher** | Cosine similarity via FAISS vector database |
| 5 | **Skill Gap Analyzer** | Identifies matched/missing skills with partial credits |
| 6 | **Scoring Agent** | Weighted 4-dimension composite scoring |
| 7 | **Recommendation Agent** | Personalized learning paths & certifications |
| 8 | **Ranking Agent** | Ranks candidates against other applicants |
| 9 | **Analytics Agent** | System-wide insights & market analysis |

## 📐 Scoring Algorithm

```
Overall Score = (Skill Match × 40%) + (Semantic × 30%) + (Experience × 20%) + (Education × 10%)
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip

### Installation & Setup

```bash
# 1. Navigate to project directory
cd "project-3(prodapt)"

# 2. Install dependencies (this may take a few minutes - downloads ML models)
pip install -r requirements.txt

# 3. Initialize database & pre-load models
python initialize.py

# 4. Start Backend API (Terminal 1)
python -m uvicorn backend.main:app --reload --port 8000

# 5. Start Modern UI (Terminal 2)
cd frontend
python -m http.server 8501
```

### Using the Windows batch scripts:
```
start_backend.bat    # Installs deps + starts backend
start_frontend.bat   # Starts Streamlit UI
```

### Access the Application
- **🎨 Modern Web UI**: http://localhost:8501
- **📡 FastAPI Docs**: http://localhost:8000/docs
- **🔧 API ReDoc**: http://localhost:8000/redoc

## 📁 Project Structure

```
project-3(prodapt)/
├── backend/
│   ├── agents/
│   │   ├── state.py              # Shared AgentState TypedDict
│   │   ├── resume_parser.py      # Agent 1: Resume parsing
│   │   ├── jd_analyzer.py        # Agent 2: JD analysis
│   │   ├── embedding_agent.py    # Agents 3 & 4: Embeddings + similarity
│   │   ├── skill_gap_agent.py    # Agent 5: Skill gap analysis
│   │   ├── scoring_agent.py      # Agent 6: Composite scoring
│   │   ├── recommendation_agent.py # Agent 7: Recommendations
│   │   └── analytics_agent.py    # Agents 8 & 9: Ranking + analytics
│   ├── utils/
│   │   └── document_parser.py    # PDF/DOCX/TXT extraction
│   ├── config.py                 # App configuration
│   ├── database.py               # SQLAlchemy models
│   ├── vector_store.py           # FAISS vector database
│   ├── workflow.py               # LangGraph orchestration
│   └── main.py                   # FastAPI application
├── frontend/
│   ├── assets/               # Image assets & icons
│   ├── css/                  # Modern styling (glassmorphism)
│   ├── js/                   # Core application logic
│   └── index.html            # Main entry point
├── initialize.py             # Setup script
├── requirements.txt              # Dependencies
├── start_backend.bat             # Windows: start backend
├── start_frontend.bat            # Windows: start frontend
└── .env                          # Environment config
```

## 💻 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/resumes/upload` | Upload resume (file or text) |
| GET  | `/api/resumes` | List all resumes |
| GET  | `/api/resumes/{id}` | Get resume details |
| POST | `/api/jobs` | Create job description |
| GET  | `/api/jobs` | List all jobs |
| POST | `/api/evaluate/sync` | Evaluate resume ↔ job (synchronous) |
| POST | `/api/evaluate` | Evaluate (async background) |
| GET  | `/api/evaluations/{id}` | Get evaluation results |
| GET  | `/api/rankings/{job_id}` | Get candidate rankings |
| GET  | `/api/analytics` | System analytics |

## 🛠️ Configuration

Edit `.env` file to customize:
- `OPENAI_API_KEY` — Optional for GPT-powered LLM features
- `EMBEDDING_MODEL` — Sentence-transformer model name
- `VECTOR_DB_TYPE` — `faiss` or `chroma`
- `DATABASE_URL` — Database connection string

## 🧪 Sample Usage

```python
import httpx

# Upload a resume
with open("resume.pdf", "rb") as f:
    resp = httpx.post("http://localhost:8000/api/resumes/upload",
                      files={"file": f})
resume_id = resp.json()["id"]

# Create a job description
resp = httpx.post("http://localhost:8000/api/jobs", json={
    "title": "Senior ML Engineer",
    "description_text": "We need Python, PyTorch, LangChain, AWS..."
})
job_id = resp.json()["id"]

# Evaluate!
resp = httpx.post("http://localhost:8000/api/evaluate/sync", json={
    "resume_id": resume_id,
    "job_id": job_id
})
print(f"Overall Score: {resp.json()['overall_score']}/100")
```

## 📊 Features

- ✅ **Multi-format support**: PDF, DOCX, TXT resumes
- ✅ **9 specialized AI agents** orchestrated by LangGraph
- ✅ **Semantic similarity** via FAISS + sentence-transformers
- ✅ **Skill extraction** from 7 technology categories (300+ skills)
- ✅ **Partial skill credit** for equivalent technologies  
- ✅ **4-dimension weighted scoring** (Skill + Semantic + Experience + Education)
- ✅ **Candidate ranking** against all applicants for a job
- ✅ **Actionable recommendations** with certifications & learning paths
- ✅ **Interactive analytics** dashboard with Plotly charts
- ✅ **RESTful API** with FastAPI and automatic OpenAPI docs
- ✅ **Modern Web UI** built with HTML5, CSS3, and JavaScript (Port 8501)
