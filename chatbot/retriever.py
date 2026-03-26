from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-base-en-v1.5")
CHROMA_PERSIST_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", "data/vectorstore"))
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION_NAME", "chipathon_docs")
TOP_K = int(os.getenv("TOP_K_RESULTS", "5"))
CONFIDENCE_THRESHOLD = float(os.getenv("RETRIEVAL_CONFIDENCE_THRESHOLD", "0.45"))


@dataclass
class RetrievedChunk:
    text: str
    source_url: str
    title: str
    section_heading: str
    doc_type: str
    score: float

    @property
    def citation(self) -> str:
        return f"{self.title} — {self.section_heading} | {self.source_url}"

    @property
    def short_citation(self) -> str:
        return f"{self.title}: {self.section_heading}"


class ChipathonRetriever:

    def __init__(self):
        self._init_clients()

    def _init_clients(self) -> None:
        if not hasattr(self, "_model"):
            self._model = SentenceTransformer(EMBED_MODEL)

        client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
        self._collection = client.get_or_create_collection(
            name=CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )

    def _embed_query(self, query: str) -> list[float]:
        # BGE query prefix differs from document prefix
        prefixed = f"Represent this sentence for searching relevant passages: {query}"
        return self._model.encode(prefixed, normalize_embeddings=True).tolist()

    def retrieve(
        self,
        query: str,
        top_k: int = TOP_K,
        doc_type_filter: str | None = None,
    ) -> tuple[list[RetrievedChunk], float]:
        if self._collection.count() == 0:
            return [], 0.0

        query_embedding = self._embed_query(query)

        if not query_embedding:
            print("Warning: Query embedding returned empty. Returning no results.")
            return [], 0.0

        where_filter = {"doc_type": doc_type_filter} if doc_type_filter else None

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self._collection.count()),
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        if not results or not results.get("distances") or len(results["distances"]) == 0:
            return [], 0.0

        chunks: list[RetrievedChunk] = []
        distances = results["distances"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            # ChromaDB cosine distance is in [0, 2]; convert to similarity [0, 1]
            similarity = 1.0 - (dist / 2.0)
            chunks.append(
                RetrievedChunk(
                    text=doc,
                    source_url=meta.get("source_url", ""),
                    title=meta.get("title", "Unknown"),
                    section_heading=meta.get("section_heading", ""),
                    doc_type=meta.get("doc_type", "unknown"),
                    score=round(similarity, 4),
                )
            )

        max_confidence = max((c.score for c in chunks), default=0.0)
        return chunks, max_confidence

    def is_confident(self, confidence: float) -> bool:
        return confidence >= CONFIDENCE_THRESHOLD
