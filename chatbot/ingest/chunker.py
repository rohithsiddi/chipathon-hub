"""
Reads raw JSON documents from scraper.py and splits them into overlapping
chunks that preserve heading context and source metadata.

Run: python -m chatbot.ingest.chunker
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import click
from rich.console import Console
from rich.progress import track

console = Console()

RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")
CHUNKS_FILE = PROCESSED_DATA_DIR / "chunks.jsonl"

MAX_CHARS = 1200
OVERLAP_CHARS = 150
MIN_CHARS = 80

CODE_FENCE_RE = re.compile(r'^```', re.MULTILINE)
HEADING_PATTERN = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)


@dataclass
class Chunk:
    text: str
    source_url: str
    title: str
    section_heading: str
    doc_type: str
    chunk_index: int
    metadata: dict


def clean_text(text: str) -> str:
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    text = re.sub(r'\s*¶\s*', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = '\n'.join(line.rstrip() for line in text.splitlines())
    return text.strip()


def extract_sections(content: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    last_heading = "Introduction"
    last_pos = 0

    for match in HEADING_PATTERN.finditer(content):
        section_body = content[last_pos:match.start()].strip()
        if section_body:
            sections.append((last_heading, section_body))
        last_heading = match.group(2).strip()
        last_pos = match.end()

    final_body = content[last_pos:].strip()
    if final_body:
        sections.append((last_heading, final_body))

    return sections


def _inside_code_block(text: str, pos: int) -> bool:
    fences = [m.start() for m in CODE_FENCE_RE.finditer(text) if m.start() < pos]
    return len(fences) % 2 == 1


def chunk_text(text: str, max_chars: int, overlap: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))

        if end >= len(text):
            remainder = text[start:].strip()
            if remainder:
                chunks.append(remainder)
            break

        # Don't cut inside a fenced code block — push to the closing fence
        if _inside_code_block(text, end):
            closing = text.find("```", end)
            end = min(closing + 3 if closing != -1 else len(text), len(text))

        break_pos = text.rfind("\n\n", start, end)
        if break_pos <= start:
            break_pos = text.rfind(". ", start, end)
        if break_pos <= start:
            break_pos = end

        chunk = text[start:break_pos].strip()
        if chunk:
            chunks.append(chunk)

        start = max(break_pos - overlap, start + 1)

    return chunks


def process_document(raw: dict) -> list[Chunk]:
    content = raw.get("content", "").strip()
    source_url = raw.get("source_url", "")
    title = raw.get("title", "Untitled")
    doc_type = raw.get("doc_type", "unknown")
    metadata = raw.get("metadata", {})

    if not content:
        return []

    content = clean_text(content)
    sections = extract_sections(content)
    chunks: list[Chunk] = []
    chunk_idx = 0

    for section_heading, section_text in sections:
        prefix = f"**{section_heading}**\n\n"
        sub_chunks = chunk_text(section_text, max_chars=MAX_CHARS - len(prefix), overlap=OVERLAP_CHARS)

        for sub in sub_chunks:
            full_text = (prefix + sub).strip()
            if len(full_text) < MIN_CHARS:
                continue

            chunks.append(Chunk(
                text=full_text,
                source_url=source_url,
                title=title,
                section_heading=section_heading,
                doc_type=doc_type,
                chunk_index=chunk_idx,
                metadata=metadata,
            ))
            chunk_idx += 1

    return chunks


@click.command()
@click.option("--raw-dir", default=str(RAW_DATA_DIR), help="Directory with raw JSON documents")
@click.option("--output-file", default=str(CHUNKS_FILE), help="Output JSONL file for chunks")
def main(raw_dir: str, output_file: str):
    """Chunk all raw documents and write to JSONL."""
    raw_path = Path(raw_dir)
    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    console.rule("[bold blue]Chipathon Chunker[/bold blue]")

    json_files = list(raw_path.rglob("*.json"))
    if not json_files:
        console.print(f"[yellow]No JSON files found in {raw_dir}. Run scraper first.[/yellow]")
        return

    console.print(f"[cyan]Found {len(json_files)} raw documents[/cyan]")

    total_chunks = 0
    with open(out_path, "w", encoding="utf-8") as out_f:
        for json_file in track(json_files, description="Chunking...", console=console):
            try:
                with open(json_file, encoding="utf-8") as f:
                    raw = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                console.print(f"[yellow]Skipping {json_file.name}: {e}[/yellow]")
                continue

            chunks = process_document(raw)
            for chunk in chunks:
                out_f.write(
                    json.dumps(
                        {
                            "text": chunk.text,
                            "source_url": chunk.source_url,
                            "title": chunk.title,
                            "section_heading": chunk.section_heading,
                            "doc_type": chunk.doc_type,
                            "chunk_index": chunk.chunk_index,
                            "metadata": chunk.metadata,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
            total_chunks += len(chunks)

    console.rule()
    console.print(f"[green]{total_chunks} chunks written to {out_path}[/green]")
    console.print("\nNext: [bold]python -m chatbot.ingest.embedder[/bold]")


if __name__ == "__main__":
    main()
