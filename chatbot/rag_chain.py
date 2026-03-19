"""
chatbot/rag_chain.py

LangGraph state machine implementing the Ask Chipathon RAG flow:

  [Query] → [Retrieve] → [Confidence Check]
                                ↓              ↓
                         [High: Generate   [Low: Triage
                          with citations]   fallback]

The fallback node does NOT hallucinate — it returns a structured triage
message asking the user for specific logs/config details.
"""

from __future__ import annotations

import os
from typing import TypedDict, Annotated

from google import genai
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from chatbot.retriever import ChipathonRetriever, RetrievedChunk

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-1.5-pro")
CONFIDENCE_THRESHOLD = float(os.getenv("RETRIEVAL_CONFIDENCE_THRESHOLD", "0.45"))

# ── State ─────────────────────────────────────────────────────────────────────

class RAGState(TypedDict):
    query: str
    chunks: list[RetrievedChunk]
    confidence: float
    answer: str
    citations: list[str]
    is_fallback: bool
    related_topics: list[str]


# ── Prompts ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are Ask Chipathon — an expert assistant for IEEE SSCS Chipathon participants
using OpenROAD-based EDA flows to go from RTL to GDSII.

Rules:
1. Answer ONLY using the provided context. Do not use prior knowledge beyond chip design basics.
2. Every factual claim must be grounded in the context.
3. Always cite which source(s) you used at the end of your answer.
4. If the context doesn't contain enough information, say so clearly — do not guess.
5. Be concise and actionable. Participants are debugging under time pressure.
6. Use markdown formatting (code blocks for commands, bullet lists for steps).
"""

ANSWER_PROMPT_TEMPLATE = """Context from Chipathon/OpenROAD knowledge base:

{context}

---

Answer the following question using ONLY the context above. Cite your sources.

Question: {query}

Answer:"""

TRIAGE_PROMPT_TEMPLATE = """You are Ask Chipathon, a strict technical assistant for the OpenROAD EDA flow. You could NOT find reliable information in the knowledge base to answer this question confidently (retrieval confidence: {confidence:.2f}).

Question: {query}

Generate a structured triage response. 

If the question is completely unrelated to chip design, OpenROAD, or the Chipathon (e.g. baking, weather, general chat), simply state that you only answer questions related to the Chipathon and OpenROAD flow.

If the question IS related to chip design/Chipathon:
1. State you don't have a reliable answer in the current knowledge base.
2. List 2-4 specific technical pieces of information the user should gather (e.g., OpenROAD log snippets, specific `.tcl` config values, `.rpt` metric values) to get better help from human mentors on Discord.
3. Suggest 2-3 related EDA topics they could search for instead.

Format your response as:
⚠️  Low confidence — I don't have a reliable answer for this.

**To get help, please share:**
[numbered list of specific information to gather]

**→ Related topics that might help:**
[bullet list of related search terms]
"""


# ── Nodes ─────────────────────────────────────────────────────────────────────

def retrieve_node(state: RAGState) -> RAGState:
    """Retrieve relevant chunks from ChromaDB."""
    retriever = ChipathonRetriever()
    chunks, confidence = retriever.retrieve(state["query"])
    return {**state, "chunks": chunks, "confidence": confidence}


def confidence_router(state: RAGState) -> str:
    """Route based on retrieval confidence."""
    if state["confidence"] >= CONFIDENCE_THRESHOLD:
        return "generate"
    return "fallback"


def generate_node(state: RAGState) -> RAGState:
    """Generate an answer using Gemini with retrieved context."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Build context string with source labels
    context_parts = []
    for i, chunk in enumerate(state["chunks"], 1):
        context_parts.append(
            f"[Source {i}: {chunk.short_citation}]\n{chunk.text}"
        )
    context = "\n\n---\n\n".join(context_parts)

    prompt = ANSWER_PROMPT_TEMPLATE.format(
        context=context,
        query=state["query"],
    )

    response = client.models.generate_content(
        model=CHAT_MODEL,
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
        )
    )
    answer = response.text.strip()

    citations = [
        f"[{i}] {chunk.citation}"
        for i, chunk in enumerate(state["chunks"], 1)
    ]

    return {
        **state,
        "answer": answer,
        "citations": citations,
        "is_fallback": False,
        "related_topics": [],
    }


def fallback_node(state: RAGState) -> RAGState:
    """Generate a structured triage fallback when confidence is low."""
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = TRIAGE_PROMPT_TEMPLATE.format(
        confidence=state["confidence"],
        query=state["query"],
    )

    response = client.models.generate_content(
        model=CHAT_MODEL,
        contents=prompt
    )
    triage_text = response.text.strip()

    # Extract related topics from the chunks we did find (even if low confidence)
    related_topics = list({
        chunk.section_heading
        for chunk in state["chunks"][:3]
        if chunk.section_heading and chunk.score > 0.2
    })

    return {
        **state,
        "answer": triage_text,
        "citations": [],
        "is_fallback": True,
        "related_topics": related_topics,
    }


# ── Graph ──────────────────────────────────────────────────────────────────────

def build_rag_graph() -> StateGraph:
    graph = StateGraph(RAGState)

    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    graph.add_node("fallback", fallback_node)

    graph.set_entry_point("retrieve")
    graph.add_conditional_edges(
        "retrieve",
        confidence_router,
        {"generate": "generate", "fallback": "fallback"},
    )
    graph.add_edge("generate", END)
    graph.add_edge("fallback", END)

    return graph.compile()


# ── Public API ────────────────────────────────────────────────────────────────

_graph = None


def ask(query: str) -> RAGState:
    """
    Main entry point: ask a question and get back a RAGState with
    answer, citations, confidence, and is_fallback flag.

    Usage:
        from chatbot.rag_chain import ask
        result = ask("How do I fix DRC errors?")
        print(result["answer"])
    """
    global _graph
    if _graph is None:
        _graph = build_rag_graph()

    initial_state: RAGState = {
        "query": query,
        "chunks": [],
        "confidence": 0.0,
        "answer": "",
        "citations": [],
        "is_fallback": False,
        "related_topics": [],
    }
    return _graph.invoke(initial_state)
