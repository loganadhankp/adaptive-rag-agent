# Adaptive RAG Agent

An advanced, self-reflecting Retrieval-Augmented Generation (RAG) system built with LangGraph, FastAPI, and Streamlit. The agent intelligently routes queries, evaluates retrieved documents for relevance, assesses its own answers for quality, and iteratively refines its search strategies or falls back to web search when necessary.

[![CI](https://github.com/<OWNER>/<REPO>/actions/workflows/ci.yml/badge.svg)](https://github.com/<OWNER>/<REPO>/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-unknown-lightgrey)](#)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](#)

## Features
- **Adaptive Routing:** Routes queries to vector store or web search based on the query context.
- **Self-Reflection & Grading:** Evaluates retrieved documents for relevance and grades generated answers for helpfulness and groundedness.
- **Iterative Refinement:** Automatically rewrites queries and retries retrieval if initial results are poor.
- **Web Search Fallback:** Falls back to web search if local documents do not contain the answer.
- **Multi-modal Document Support:** Upload and process PDF, DOCX, and TXT files.
- **Interactive UI:** Chat interface with citations, sources, and step-by-step workflow visibility.

## Architecture Overview
The system uses a LangGraph state machine to coordinate the workflow. A user query is first routed by an LLM to either the vector store or web search. If routed to the vector store, documents are retrieved and graded for relevance. If relevant, an answer is generated and graded. If not relevant, the query is rewritten and retrieval is attempted again. If the answer quality is poor, the system may rewrite the query or ultimately fallback to web search.

## Prerequisites
- Python 3.11+
- OpenAI API Key (or Anthropic API Key)
- Tavily API Key (optional, for web search fallback)

## Quick Start

1. **Clone/download the repository:**
   ```bash
   git clone <repository-url>
   cd adaptive-rag-agent
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   Copy the example environment file and fill in your API keys:
   ```bash
   cp .env.example .env
   ```
   *Edit `.env` and add your `OPENAI_API_KEY`.*

5. **Run the application:**
   ```bash
   python run.py
   ```

## CI / GitHub Actions

This repository includes a GitHub Actions workflow at `.github/workflows/ci.yml` that runs unit tests, code quality checks, and deterministic Playwright E2E tests under `TEST_MODE=true` on every push and pull request to `main` and `develop`.

To enable CI badges, replace `<OWNER>/<REPO>` in the badge URLs above with your GitHub organization and repository name.

## Usage Guide
- **Knowledge Base:** Navigate to the Knowledge Base page in the frontend to upload documents (PDF, DOCX, TXT). The system will process and index them into the Chroma vector database.
- **Chat:** Use the chat interface to ask questions. The agent will retrieve relevant context from your documents or search the web.
- **Sources & Workflow:** Expand the message details to see the workflow steps taken by the agent and the sources cited for the answer.
- **Analytics:** Check the dashboard for usage statistics and retrieval performance.

## API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check endpoint. |
| `/chat` | POST | Send a message to the agent and receive a streamed or synchronous response. |
| `/documents/upload` | POST | Upload a document to the knowledge base. |
| `/documents` | GET | List all indexed documents. |
| `/documents/{doc_id}` | DELETE | Remove a document from the knowledge base. |

## Project Structure
```text
adaptive-rag-agent/
├── backend/               # FastAPI application & AI pipelines
│   ├── agents/            # LLM & vector store factory
│   ├── database/          # SQLite persistence & conversation repository
│   ├── prompts/           # Prompts (sufficiency, generation, grading)
│   ├── routers/           # FastAPI routers (/chat, /kb, /analytics)
│   ├── services/          # Business logic services
│   ├── workflow/          # LangGraph state graph, nodes, and routing
│   ├── config.py          # App settings (Pydantic BaseSettings)
│   ├── main.py            # FastAPI entrypoint
│   └── models.py          # Data models and schemas
├── frontend/              # Streamlit interactive UI
│   ├── components/        # UI components (chat window, sidebar)
│   ├── api_client.py      # HTTP & SSE client for FastAPI
│   ├── app.py             # Streamlit application entrypoint
│   └── styles.py          # Modern CSS styling
├── data/                  # Persistent data storage
│   ├── documents/         # Uploaded documents
│   ├── vector_db/         # ChromaDB persistence
│   └── chat_history.db    # SQLite conversation database
├── tests/                 # Automated test suite (unit, integration, security)
├── requirements.txt       # Project dependencies
├── run.py                 # Startup script (launches FastAPI & Streamlit)
└── README.md              # Project documentation
```

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google Gemini API key (recommended) | None |
| `LLM_PROVIDER` | LLM provider to use (`gemini`, `openai`, `anthropic`) | `gemini` |
| `LLM_MODEL` | LLM model identifier | `gemini-3.5-flash-lite` |
| `EMBEDDING_MODEL` | Embedding model identifier | `models/gemini-embedding-001` |
| `CHUNK_SIZE` | Text chunk size for splitting | 1000 |
| `CHUNK_OVERLAP` | Overlap between text chunks | 200 |
| `MAX_RETRIES` | Max query rewrite retries | 2 |

## Tech Stack
- **Frameworks:** FastAPI, Streamlit, LangChain, LangGraph
- **Vector DB:** ChromaDB
- **LLMs:** Google Gemini (Gemini 2.5/3.5), OpenAI, Anthropic
- **Search:** Tavily API

## Deployment Notes
- For production, use a production-grade ASGI server like Gunicorn with Uvicorn workers.
- The default SQLite/Chroma setup is for development. Consider PostgreSQL + pgvector for production deployments.
- Ensure appropriate authentication and rate limiting are added to the FastAPI endpoints.

## License
MIT License
