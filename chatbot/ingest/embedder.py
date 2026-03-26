"""
Reads chunks.jsonl from chunker.py, generates BGE embeddings locally,
and stores them in a persistent ChromaDB collection.

Run: python -m chatbot.ingest.embedder
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import chromadb
import click
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import track

load_dotenv()

console = Console()

EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-base-en-v1.5")
CHROMA_PERSIST_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", "data/vectorstore"))
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION_NAME", "chipathon_docs")
CHUNKS_FILE = Path("data/processed/chunks.jsonl")

BATCH_SIZE = 64


def make_chunk_id(source_url: str, chunk_index: int, text: str) -> str:
    """Stable content-based ID — prevents duplicates on re-runs."""
    key = f"{source_url}::{chunk_index}::{text[:120]}"
    return hashlib.md5(key.encode()).hexdigest()


def get_embeddings(model: SentenceTransformer, texts: list[str]) -> list[list[float]]:
    # BGE models work best with this prompt prefix for documents
    prefixed = [f"Represent this sentence for searching relevant passages: {t}" for t in texts]
    return model.encode(prefixed, normalize_embeddings=True).tolist()


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

    console.rule("[bold blue]Chipathon Embedder[/bold blue]")
    console.print(f"[cyan]Loading model {EMBED_MODEL}...[/cyan]")
    model = SentenceTransformer(EMBED_MODEL)

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
        metadata={"hnsw:space": "cosine"},
    )

    chunks = []
    with open(chunks_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))

    console.print(f"[cyan]Loaded {len(chunks)} chunks[/cyan]")

    all_chunk_ids = [
        make_chunk_id(c["source_url"], c["chunk_index"], c["text"]) for c in chunks
    ]
    existing_ids = set(col.get()["ids"])
    new_pairs = [(cid, c) for cid, c in zip(all_chunk_ids, chunks) if cid not in existing_ids]

    if not new_pairs:
        console.print("[green]All chunks already embedded. Nothing to do.[/green]")
        return

    console.print(f"[cyan]Embedding {len(new_pairs)} new chunks (skipping {len(chunks) - len(new_pairs)} already indexed)...[/cyan]")

    for batch_start in track(
        range(0, len(new_pairs), BATCH_SIZE),
        description="Embedding batches...",
        console=console,
    ):
        batch_pairs = new_pairs[batch_start: batch_start + BATCH_SIZE]
        batch_ids = [p[0] for p in batch_pairs]
        batch_chunks = [p[1] for p in batch_pairs]
        texts = [c["text"] for c in batch_chunks]

        embeddings = get_embeddings(model, texts)

        metadatas = []
        for c in batch_chunks:
            meta = c.get("metadata", {})
            metadatas.append({
                "source_url": c["source_url"],
                "title": c["title"],
                "section_heading": c["section_heading"],
                "doc_type": c["doc_type"],
                "chunk_index": str(c["chunk_index"]),
                "issue_number": str(meta.get("issue_number", "")),
                "labels": ",".join(meta.get("labels", [])) if isinstance(meta.get("labels"), list) else "",
                "repo": meta.get("repo", ""),
            })

        col.add(
            ids=batch_ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

    console.rule()
    console.print(f"[green]ChromaDB collection '{collection}' has {col.count()} vectors[/green]")
    console.print(f"[dim]Stored at: {persist_path}[/dim]")
    console.print("\nReady! Run: [bold]ask-chipathon \"your question here\"[/bold]")


if __name__ == "__main__":
    main()
