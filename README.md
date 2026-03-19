# Chipathon Knowledge Hub + Ask Chipathon Chatbot

> A GSoC 2026 PoC — centralized documentation hub and Gemini-powered RAG chatbot for IEEE SSCS Chipathon participants using OpenROAD-based flows.

---

## 🗂️ Project Structure

```
chipathon-hub/
├── hub/                    ← MkDocs Material knowledge site
│   ├── docs/               ← Markdown documentation pages
│   └── mkdocs.yml          ← Site configuration
│
├── chatbot/                ← Ask Chipathon RAG chatbot
│   ├── ingest/             ← Scraper → chunker → embedder pipeline
│   ├── retriever.py        ← ChromaDB similarity search
│   ├── rag_chain.py        ← LangGraph RAG with fallback logic
│   ├── cli.py              ← ask-chipathon CLI
│   └── eval/               ← Evaluation harness
│
├── data/                   ← Local data (gitignored)
│   ├── raw/                ← Fetched docs/issues
│   ├── processed/          ← Chunked text with metadata
│   └── vectorstore/        ← ChromaDB persistent store
│
└── .github/workflows/      ← Auto-rebuild index on doc changes
```

---

## 🚀 Quick Start

### 1. Setup (uv)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install deps
uv venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows

uv pip install -e .
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and set your GEMINI_API_KEY and GITHUB_TOKEN
```

### 3. Ingest Documents

```bash
# Fetch OpenROAD docs + GitHub issues → embed into ChromaDB
chipathon-ingest
```

### 4. Ask Questions

```bash
ask-chipathon "How do I fix DRC errors in OpenROAD?"
ask-chipathon "What does the floorplan stage produce?"
ask-chipathon "How do I interpret timing reports?"
```

### 5. Run the Knowledge Hub locally

```bash
cd hub
mkdocs serve
# Open http://127.0.0.1:8000
```

### 6. Run the Eval Harness

```bash
python chatbot/eval/eval_harness.py
```

---

## 🤖 Chatbot Architecture

```
Query → ChromaDB Retriever → Confidence Check
                                    ↓              ↓
                             [High confidence]  [Low confidence]
                             Gemini 1.5 Pro     Triage fallback
                             answer + citations  + log request
```

**Key design decisions:**
- **Gemini** (`gemini-1.5-pro`) for generation, `text-embedding-004` for embeddings
- **LangGraph** state machine for structured RAG flow with proper fallback
- **ChromaDB** for persistent, metadata-filtered vector search
- **Section-level citations** — every answer cites the exact doc section

---

## 📚 Data Sources

| Source | Content | Method |
|--------|---------|--------|
| [OpenROAD Docs](https://openroad.readthedocs.io) | Official tool docs, FAQs | Web scrape |
| [ORFS GitHub](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts) | Flow scripts, READMEs | GitHub API |
| [OpenROAD Issues](https://github.com/The-OpenROAD-Project/OpenROAD/issues) | Real debugging Q&A | GitHub API |
| [OpenROAD Discussions](https://github.com/The-OpenROAD-Project/OpenROAD/discussions) | Community answers | GitHub API |

---

## 🧪 Evaluation

The eval harness tests 30 Chipathon-style questions against:
- **Citation coverage** — does every answer cite a real source?
- **Groundedness** — is the answer supported by retrieved context?
- **No-answer correctness** — does the bot correctly say "I don't know" when evidence is missing?

---

## 📄 License

Apache 2.0 — consistent with the OpenROAD project.
