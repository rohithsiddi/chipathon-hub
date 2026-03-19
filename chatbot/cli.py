"""
chatbot/cli.py

Rich-formatted CLI for Ask Chipathon.

Usage:
    ask-chipathon "How do I fix DRC errors?"
    ask-chipathon --interactive
    ask-chipathon --debug "What is CORE_UTILIZATION?"
"""

from __future__ import annotations

import sys

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich import box

console = Console()

BANNER = """
   ╔═══════════════════════════════════════════╗
   ║   🤖  Ask Chipathon  |  OpenROAD RAG Bot  ║
   ║   Powered by Gemini 1.5 Pro + ChromaDB    ║
   ╚═══════════════════════════════════════════╝
"""


def render_answer(result: dict) -> None:
    """Render the RAG result to the terminal with Rich formatting."""
    is_fallback = result.get("is_fallback", False)
    confidence = result.get("confidence", 0.0)
    chunks = result.get("chunks", [])
    citations = result.get("citations", [])
    answer = result.get("answer", "No answer generated.")
    related = result.get("related_topics", [])

    # ── Confidence badge ──
    if is_fallback:
        badge = f"[bold red]⚠️  Low confidence ({confidence:.2f})[/bold red]"
    else:
        badge = f"[bold green]📖 Retrieved {len(chunks)} sources (confidence: {confidence:.2f})[/bold green]"

    console.print(badge)
    console.print()

    # ── Main answer ──
    answer_panel = Panel(
        Markdown(answer),
        title="[bold]Answer[/bold]",
        border_style="blue" if not is_fallback else "yellow",
        padding=(1, 2),
    )
    console.print(answer_panel)

    # ── Citations (only for high-confidence answers) ──
    if citations:
        console.print()
        console.print("[dim]📎 Sources:[/dim]")
        for citation in citations:
            console.print(f"  [dim]{citation}[/dim]")

    # ── Related topics from partial retrieval ──
    if related:
        console.print()
        console.print("[dim]💡 Related topics:[/dim]")
        for topic in related:
            console.print(f"  [dim]• {topic}[/dim]")


def render_debug(result: dict) -> None:
    """Show debug info: retrieved chunks + scores."""
    chunks = result.get("chunks", [])
    if not chunks:
        console.print("[yellow]No chunks retrieved.[/yellow]")
        return

    table = Table(
        title="Retrieved Chunks",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Score", style="green", width=6)
    table.add_column("Type", style="blue", width=12)
    table.add_column("Title", style="white", width=30)
    table.add_column("Section", style="dim", width=25)
    table.add_column("Preview", style="dim", width=40)

    for chunk in chunks:
        table.add_row(
            f"{chunk['score']:.3f}" if isinstance(chunk, dict) else f"{chunk.score:.3f}",
            chunk.get("doc_type", "?") if isinstance(chunk, dict) else chunk.doc_type,
            (chunk.get("title", "?") if isinstance(chunk, dict) else chunk.title)[:28],
            (chunk.get("section_heading", "") if isinstance(chunk, dict) else chunk.section_heading)[:23],
            (chunk.get("text", "")[:80] if isinstance(chunk, dict) else chunk.text[:80]) + "...",
        )

    console.print(table)


@click.command()
@click.argument("query", required=False)
@click.option("--interactive", "-i", is_flag=True, default=False, help="Run in interactive mode")
@click.option("--debug", "-d", is_flag=True, default=False, help="Show retrieved chunks + scores")
@click.option("--ingest", is_flag=True, default=False, help="Run full ingest pipeline first")
def main(query: str | None, interactive: bool, debug: bool, ingest: bool) -> None:
    """
    Ask Chipathon — Gemini-powered Q&A for IEEE SSCS Chipathon + OpenROAD flows.

    Examples:\n
        ask-chipathon "How do I fix DRC errors?"\n
        ask-chipathon --interactive\n
        ask-chipathon --debug "What is CORE_UTILIZATION?"
    """
    console.print(BANNER, style="bold cyan")

    if ingest:
        console.print("[cyan]Running ingest pipeline...[/cyan]")
        from chatbot.ingest.scraper import main as run_scraper
        from chatbot.ingest.chunker import main as run_chunker
        from chatbot.ingest.embedder import main as run_embedder
        run_scraper(standalone_mode=False)
        run_chunker(standalone_mode=False)
        run_embedder(standalone_mode=False)
        console.print()

    # Lazy import (avoids slow startup for --help)
    try:
        from chatbot.rag_chain import ask
    except Exception as e:
        console.print(f"[red]Failed to initialize RAG chain: {e}[/red]")
        console.print("[yellow]Make sure GEMINI_API_KEY is set in .env and the knowledge base is indexed.[/yellow]")
        sys.exit(1)

    def run_query(q: str) -> None:
        if not q.strip():
            return
        console.print(Rule(f"[bold]Query:[/bold] {q}", style="dim"))
        console.print()

        with console.status("[cyan]Thinking...[/cyan]", spinner="dots"):
            try:
                result = ask(q)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                return

        if debug:
            render_debug(result)
            console.print()

        render_answer(result)
        console.print()

    if interactive:
        console.print("[dim]Interactive mode. Type 'quit' or press Ctrl+C to exit.[/dim]\n")
        while True:
            try:
                q = console.input("[bold cyan]Ask Chipathon ›[/bold cyan] ").strip()
                if q.lower() in {"quit", "exit", "q"}:
                    console.print("[dim]Goodbye![/dim]")
                    break
                run_query(q)
            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]Goodbye![/dim]")
                break
    elif query:
        run_query(query)
    else:
        click.echo(click.get_current_context().get_help())


if __name__ == "__main__":
    main()
