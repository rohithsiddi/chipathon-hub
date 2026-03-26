# Chipathon Knowledge Hub + Ask Chipathon

A GSoC 2026 proof-of-concept for IEEE SSCS Chipathon — a documentation hub paired with a RAG chatbot that answers questions about OpenROAD-based RTL-to-GDSII flows.

Live demos: [Knowledge Hub](https://rohithsiddi.github.io/chipathon-hub/) · [API on HF Spaces](https://huggingface.co/spaces/rohithsiddi/chipathon-api)

---

## What this is

Chipathon participants often get stuck on the same problems — DRC errors, timing failures, flow configuration — and end up digging through scattered docs, GitHub issues, and Discord threads to find answers. This project centralizes that knowledge and makes it searchable through a chatbot.

The chatbot retrieves relevant content from OpenROAD documentation, GitHub issues, and community discussions, then generates grounded answers with source citations. If it can't find a reliable answer, it falls back to a structured triage response with suggestions for getting help from mentors.

## Project layout

```
├── hub/                    # MkDocs Material knowledge site
│   ├── docs/               # Markdown pages
│   └── mkdocs.yml
│
├── chatbot/
│   ├── ingest/             # scraper → chunker → embedder pipeline
│   ├── retriever.py        # ChromaDB vector search
│   ├── rag_chain.py        # LangGraph RAG with confidence-based routing
│   ├── cli.py              # ask-chipathon CLI
│   └── eval/               # evaluation harness
│
├── data/
│   ├── raw/                # fetched documents (gitignored)
│   ├── processed/          # chunked text with metadata (gitignored)
│   └── vectorstore/        # ChromaDB persistent store (committed)
│
└── .github/workflows/      # CI: rebuild index weekly, deploy hub + API
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Copy `.env.example` to `.env` and set:
- `OPENAI_API_KEY` — for answer generation (gpt-4o-mini)
- `GITHUB_TOKEN` — for fetching issues and discussions (optional but recommended)
- `HF_TOKEN` — only needed for CI deployment

## Running locally

**Build the knowledge base** (scrape docs, chunk, embed):
```bash
python -m chatbot.ingest.scraper
python -m chatbot.ingest.chunker
python -m chatbot.ingest.embedder
```

**Ask questions:**
```bash
ask-chipathon "How do I fix setup timing violations?"
ask-chipathon "What does the floorplan stage produce?"
ask-chipathon "How do I interpret a timing report?"
```

**Run the knowledge hub locally:**
```bash
cd hub && mkdocs serve
```

**Run the eval harness:**
```bash
python -m chatbot.eval.eval_harness
```

## Architecture

The RAG pipeline uses a LangGraph state machine with confidence-based routing:

```
Query
  → BGE embeddings (local, BAAI/bge-base-en-v1.5)
  → ChromaDB cosine similarity search
  → confidence score
      ≥ 0.45  →  GPT-4o-mini generates answer with citations
      < 0.45  →  structured fallback with triage guidance
```

Key choices:
- **BGE embeddings** run locally — no API calls, no rate limits, no cost
- **GPT-4o-mini** for generation — fast and cheap enough for a prototype
- **LangGraph** for the RAG flow so routing logic is explicit and testable
- **ChromaDB** with cosine similarity, persistent to disk so it can be bundled in Docker

## Data sources

The knowledge base pulls from:

| Source | What we get |
|--------|-------------|
| OpenROAD ReadTheDocs | Official docs, FAQs |
| ORFS ReadTheDocs | Flow tutorial, build guides |
| OpenROAD GitHub markdown (`src/`, `docs/`) | Per-tool READMEs (placement, routing, CTS, STA, PDN…) |
| ORFS GitHub markdown (`docs/`) | Flow variables, adding new designs, platform guides |
| OpenROAD GitHub Issues (closed) | Real debugging Q&A with resolutions |
| ORFS GitHub Issues (closed) | Flow-specific debugging cases |
| OpenROAD GitHub Discussions | Community answers |
| ORFS GitHub Discussions | Community answers |

The index rebuilds automatically every Sunday via GitHub Actions.

## Evaluation

The eval harness runs a set of Chipathon-style questions and measures:
- **Citation coverage** — does every answer cite a source?
- **Groundedness** — is the answer actually supported by the retrieved context?
- **No-answer correctness** — does the bot fall back appropriately when it shouldn't answer?
- **Average retrieval confidence** — how similar are retrieved chunks to the query?

## Deployment

The knowledge hub deploys to GitHub Pages via `deploy-hub.yml`. The API backend deploys as a Docker container to Hugging Face Spaces via `deploy-api.yml`. Both trigger automatically on push to `main`.

## License

Apache 2.0, consistent with the OpenROAD project.
