from __future__ import annotations

import os
from typing import TypedDict

from openai import OpenAI
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from chatbot.retriever import ChipathonRetriever, RetrievedChunk

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
CONFIDENCE_THRESHOLD = float(os.getenv("RETRIEVAL_CONFIDENCE_THRESHOLD", "0.45"))


class RAGState(TypedDict):
    query: str
    intent: str  # "answerable" | "code_gen" | "off_topic" | "meta"
    chunks: list[RetrievedChunk]
    confidence: float
    answer: str
    citations: list[str]
    is_fallback: bool
    related_topics: list[str]


INTENT_SYSTEM_PROMPT = """Classify the user query into exactly one category:
- answerable: a question about OpenROAD, ORFS, chip design, EDA flows, PDKs, timing, or the Chipathon
- code_gen: a request to write, generate, implement, or create code, scripts, or design files
- off_topic: unrelated to chip design or EDA (cooking, sports, general software, etc.)
- meta: a question about this chatbot (what it does, who made it, capabilities)

Reply with only the category name, nothing else."""

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

TRIAGE_PROMPT_TEMPLATE = """You are Ask Chipathon, a technical assistant specialized in the OpenROAD EDA flow and IEEE SSCS Chipathon.

Question: {query}

First, classify the question into one of these categories:
A) Off-topic or meta (e.g. "what can you do?", "who are you?", "tell me a joke", weather, cooking, etc.)
B) Vague or unclear chip design question
C) Specific chip design / OpenROAD question but not found in the knowledge base (retrieval confidence: {confidence:.2f})

Then respond accordingly:

If category A — respond ONLY with:
I'm Ask Chipathon, a technical assistant for the IEEE SSCS Chipathon. I can help with:
• Running the OpenROAD RTL-to-GDSII flow
• Debugging placement, routing, CTS, and timing issues
• Understanding OpenROAD tools and commands
• Interpreting log files and timing reports

Try asking something like: "How do I fix setup timing violations?" or "What does repair_timing do?"

If category B or C — respond with:
⚠️  I don't have a reliable answer for this in my knowledge base.

**To get help from mentors on Discord, share:**
[2-4 specific items: relevant log snippets, .tcl config values, .rpt metrics, OpenROAD version]

**→ Related topics to search:**
[2-3 relevant EDA terms]
"""


def classify_intent_node(state: RAGState) -> RAGState:
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": INTENT_SYSTEM_PROMPT},
            {"role": "user", "content": state["query"]},
        ],
        max_tokens=10,
        temperature=0,
    )
    raw = response.choices[0].message.content.strip().lower()
    intent = raw if raw in ("answerable", "code_gen", "off_topic", "meta") else "answerable"
    return {**state, "intent": intent}


def intent_router(state: RAGState) -> str:
    if state["intent"] == "answerable":
        return "retrieve"
    return "fallback"


def retrieve_node(state: RAGState) -> RAGState:
    retriever = ChipathonRetriever()
    chunks, confidence = retriever.retrieve(state["query"])
    return {**state, "chunks": chunks, "confidence": confidence}


def confidence_router(state: RAGState) -> str:
    if state["confidence"] >= CONFIDENCE_THRESHOLD:
        return "generate"
    return "fallback"


def generate_node(state: RAGState) -> RAGState:
    client = OpenAI(api_key=OPENAI_API_KEY)

    context_parts = []
    for i, chunk in enumerate(state["chunks"], 1):
        context_parts.append(f"[Source {i}: {chunk.short_citation}]\n{chunk.text}")
    context = "\n\n---\n\n".join(context_parts)

    prompt = ANSWER_PROMPT_TEMPLATE.format(context=context, query=state["query"])

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    answer = response.choices[0].message.content.strip()

    citations = [
        f"[{i}] {chunk.citation}"
        for i, chunk in enumerate(state["chunks"], 1)
    ]

    return {**state, "answer": answer, "citations": citations, "is_fallback": False, "related_topics": []}


def fallback_node(state: RAGState) -> RAGState:
    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = TRIAGE_PROMPT_TEMPLATE.format(
        confidence=state["confidence"],
        query=state["query"],
    )

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    triage_text = response.choices[0].message.content.strip()

    related_topics = list({
        chunk.section_heading
        for chunk in state["chunks"][:3]
        if chunk.section_heading and chunk.score > 0.2
    })

    return {**state, "answer": triage_text, "citations": [], "is_fallback": True, "related_topics": related_topics}


def build_rag_graph() -> StateGraph:
    graph = StateGraph(RAGState)

    graph.add_node("classify", classify_intent_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    graph.add_node("fallback", fallback_node)

    graph.set_entry_point("classify")
    graph.add_conditional_edges(
        "classify",
        intent_router,
        {"retrieve": "retrieve", "fallback": "fallback"},
    )
    graph.add_conditional_edges(
        "retrieve",
        confidence_router,
        {"generate": "generate", "fallback": "fallback"},
    )
    graph.add_edge("generate", END)
    graph.add_edge("fallback", END)

    return graph.compile()


_graph = None


def ask(query: str) -> RAGState:
    global _graph
    if _graph is None:
        _graph = build_rag_graph()

    initial_state: RAGState = {
        "query": query,
        "intent": "",
        "chunks": [],
        "confidence": 0.0,
        "answer": "",
        "citations": [],
        "is_fallback": False,
        "related_topics": [],
    }
    return _graph.invoke(initial_state)
