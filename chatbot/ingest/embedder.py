"""
chatbot/ingest/embedder.py

Reads chunks.jsonl (from chunker.py), generates Gemini text-embedding-004
vectors, and stores them in a persistent ChromaDB collection.

Run:
    python -m chatbot.ingest.embedder
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import chromadb
import click
from google import genai
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import track

load_dotenv()

console = Console()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
CHROMA_PERSIST_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", "data/vectorstore"))
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION_NAME", "chipathon_docs")
CHUNKS_FILE = Path("data/processed/chunks.jsonl")

# Gemini embedding API: max 100 texts per batch call
BATCH_SIZE = 50
# Rate limit: max 15 requests/min on free tier
REQUEST_DELAY_S = 4.0


def get_gemini_embeddings(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using Gemini using the new SDK."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    result = client.models.embed_content(
        model=EMBED_MODEL,
        contents=texts,
        config=genai.types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
    )
    return [e.values for e in result.embeddings]


@click.command()
@click.option("--chunks-file", default=str(CHUNKS_FILE), help="JSONL file of chunks")
@click.option("--persist-dir", default=str(CHROMA_PERSIST_DIR), help="ChromaDB persistence dir")
@click.option("--collection", default=CHROMA_COLLECTION, help="ChromaDB collection name")
@click.option("--reset", is_flag=True, default=False, help="Delete and recreate the collection")
def main(chunks_file: str, persist_dir: str, collection: str, reset: bool):
    """Embed all chunks and store in ChromaDB."""
    chunks_path = Path(chunks_file)
    persist_path = Path(persist_dir)

    if not chunks_path.exists():
        console.print(f"[red]Chunks file not found: {chunks_path}. Run chunker first.[/red]")
        return

    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        console.print("[red]GEMINI_API_KEY not set in .env — cannot generate embeddings.[/red]")
        return

    console.rule("[bold blue]Chipathon Embedder[/bold blue]")

    # ── Setup ChromaDB ──
    persist_path.mkdir(parents=True, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=str(persist_path))

    if reset:
        try:
            chroma_client.delete_collection(collection)
            console.print(f"[yellow]Deleted existing collection '{collection}'[/yellow]")
        except Exception:
            pass

    col = chroma_client.get_or_create_collection(
        name=collection,
        metadata={"hnsw:space": "cosine"},  # cosine similarity
    )

    # ── Load chunks ──
    chunks = []
    with open(chunks_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))

    console.print(f"[cyan]Loaded {len(chunks)} chunks[/cyan]")

    # Check how many are already indexed
    existing_ids = set(col.get()["ids"])
    new_chunks = [c for i, c in enumerate(chunks) if str(i) not in existing_ids]
    if not new_chunks:
        console.print("[green]All chunks already embedded. Nothing to do.[/green]")
        return

    console.print(f"[cyan]Embedding {len(new_chunks)} new chunks (skipping {len(chunks) - len(new_chunks)} already indexed)...[/cyan]")

    # ── Embed in batches ──
    start_idx = len(existing_ids)
    for batch_start in track(
        range(0, len(new_chunks), BATCH_SIZE),
        description="Embedding batches...",
        console=console,
    ):
        batch = new_chunks[batch_start: batch_start + BATCH_SIZE]
        texts = [c["text"] for c in batch]

        max_retries = 3
        for attempt in range(max_retries):
            try:
                embeddings = get_gemini_embeddings(texts)
                break
            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    console.print(f"[yellow]Rate limit hit. Waiting 65s before retry (Attempt {attempt + 1}/{max_retries})...[/yellow]")
                    time.sleep(65)
                else:
                    console.print(f"[yellow]Embedding batch failed: {err_msg}. Retrying in 5s (Attempt {attempt + 1}/{max_retries})...[/yellow]")
                    time.sleep(5)
        else:
            console.print("[red]Max retries exceeded. Skipping batch.[/red]")
            continue

        ids = [str(start_idx + batch_start + j) for j in range(len(batch))]
        metadatas = [
            {
                "source_url": c["source_url"],
                "title": c["title"],
                "section_heading": c["section_heading"],
                "doc_type": c["doc_type"],
                "chunk_index": str(c["chunk_index"]),
            }
            for c in batch
        ]

        col.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        time.sleep(REQUEST_DELAY_S)

    console.rule()
    console.print(f"[green]✅ ChromaDB collection '{collection}' has {col.count()} vectors[/green]")
    console.print(f"[dim]Stored at: {persist_path}[/dim]")
    console.print("\nReady! Run: [bold]ask-chipathon \"your question here\"[/bold]")


if __name__ == "__main__":
    main()
