"""
chatbot/eval/eval_harness.py

Evaluation harness for Ask Chipathon.
Runs 30 Chipathon-style questions and produces metrics:

  - Citation Coverage    : % of answerable questions with ≥1 citation
  - Groundedness         : % of answers that mention expected topic keywords
  - No-Answer Correctness: % of out-of-domain questions that trigger fallback
  - Average Confidence   : mean retrieval confidence across all questions

Usage:
    python chatbot/eval/eval_harness.py
    python chatbot/eval/eval_harness.py --output results/eval_latest.json
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime

import click
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich import box

console = Console()

QUESTIONS_FILE = Path(__file__).parent / "questions.json"


@dataclass
class EvalResult:
    question_id: str
    question: str
    should_answer: bool
    confidence: float
    is_fallback: bool
    has_citations: bool
    answer_snippet: str = ""
    groundedness_keywords_found: list[str] = field(default_factory=list)
    groundedness_keywords_missing: list[str] = field(default_factory=list)

    @property
    def citation_ok(self) -> bool:
        """Citation coverage: answerable questions should have citations."""
        return not self.should_answer or self.has_citations

    @property
    def fallback_ok(self) -> bool:
        """No-answer correctness: unanswerable questions should trigger fallback."""
        return not self.should_answer == self.is_fallback

    @property
    def groundedness_score(self) -> float:
        """Fraction of expected keywords found in the answer."""
        total = len(self.groundedness_keywords_found) + len(self.groundedness_keywords_missing)
        if total == 0:
            return 1.0  # no keywords expected = trivially grounded
        return len(self.groundedness_keywords_found) / total


@dataclass
class EvalReport:
    timestamp: str
    total_questions: int
    answerable_count: int
    unanswerable_count: int
    citation_coverage: float      # % of answerable Qs with citations
    avg_groundedness: float       # avg keyword recall across answerable Qs
    no_answer_correctness: float  # % of unanswerable Qs that fallback
    avg_confidence: float
    results: list[EvalResult] = field(default_factory=list)


def compute_groundedness(answer: str, expected_topics: list[str]) -> tuple[list[str], list[str]]:
    """Check which expected topic keywords appear in the answer (case-insensitive)."""
    answer_lower = answer.lower()
    found = [kw for kw in expected_topics if kw.lower() in answer_lower]
    missing = [kw for kw in expected_topics if kw.lower() not in answer_lower]
    return found, missing


def run_eval(questions: list[dict], delay_s: float = 1.0) -> EvalReport:
    """Run all evaluation questions through the RAG chain."""
    from chatbot.rag_chain import ask

    results: list[EvalResult] = []
    answerable = [q for q in questions if q["should_answer"]]
    unanswerable = [q for q in questions if not q["should_answer"]]

    for q in track(questions, description="Running eval...", console=console):
        try:
            state = ask(q["question"])
        except Exception as e:
            console.print(f"[red]Error on {q['id']}: {e}[/red]")
            results.append(EvalResult(
                question_id=q["id"],
                question=q["question"],
                should_answer=q["should_answer"],
                confidence=0.0,
                is_fallback=True,
                has_citations=False,
                answer_snippet=f"ERROR: {e}",
            ))
            continue

        citations = state.get("citations", [])
        answer = state.get("answer", "")
        is_fallback = state.get("is_fallback", False)
        confidence = state.get("confidence", 0.0)
        found, missing = compute_groundedness(answer, q.get("expected_topics", []))

        results.append(EvalResult(
            question_id=q["id"],
            question=q["question"],
            should_answer=q["should_answer"],
            confidence=round(confidence, 4),
            is_fallback=is_fallback,
            has_citations=len(citations) > 0,
            answer_snippet=answer[:200],
            groundedness_keywords_found=found,
            groundedness_keywords_missing=missing,
        ))
        time.sleep(delay_s)  # rate limiting

    # ── Compute metrics ──
    ans_results = [r for r in results if r.should_answer]
    unans_results = [r for r in results if not r.should_answer]

    citation_coverage = (
        sum(1 for r in ans_results if r.has_citations) / len(ans_results)
        if ans_results else 0.0
    )
    avg_groundedness = (
        sum(r.groundedness_score for r in ans_results) / len(ans_results)
        if ans_results else 0.0
    )
    no_answer_correctness = (
        sum(1 for r in unans_results if r.is_fallback) / len(unans_results)
        if unans_results else 0.0
    )
    avg_confidence = sum(r.confidence for r in results) / len(results) if results else 0.0

    return EvalReport(
        timestamp=datetime.utcnow().isoformat(),
        total_questions=len(questions),
        answerable_count=len(answerable),
        unanswerable_count=len(unanswerable),
        citation_coverage=round(citation_coverage, 4),
        avg_groundedness=round(avg_groundedness, 4),
        no_answer_correctness=round(no_answer_correctness, 4),
        avg_confidence=round(avg_confidence, 4),
        results=results,
    )


def print_report(report: EvalReport) -> None:
    """Pretty-print the eval report to the terminal."""
    console.rule("[bold blue]Ask Chipathon — Eval Report[/bold blue]")

    # Summary metrics table
    summary = Table(title="Overall Metrics", box=box.ROUNDED, show_header=True, header_style="bold cyan")
    summary.add_column("Metric", style="white")
    summary.add_column("Score", style="green", justify="right")
    summary.add_column("Target", style="dim", justify="right")
    summary.add_column("Status", justify="center")

    metrics = [
        ("Citation Coverage", report.citation_coverage, 0.80),
        ("Avg Groundedness", report.avg_groundedness, 0.65),
        ("No-Answer Correctness", report.no_answer_correctness, 1.00),
        ("Avg Confidence", report.avg_confidence, 0.50),
    ]

    for name, score, target in metrics:
        pct = f"{score*100:.1f}%"
        status = "✅" if score >= target else "❌"
        summary.add_row(name, pct, f"≥{target*100:.0f}%", status)

    console.print(summary)
    console.print()

    # Per-question results table
    detail = Table(title="Per-Question Results", box=box.SIMPLE, header_style="bold")
    detail.add_column("ID", width=5)
    detail.add_column("Q (truncated)", width=40)
    detail.add_column("Conf", width=6, justify="right")
    detail.add_column("Fallback", width=8, justify="center")
    detail.add_column("Cited", width=6, justify="center")
    detail.add_column("Ground", width=7, justify="right")
    detail.add_column("OK", width=4, justify="center")

    for r in report.results:
        ok = "✅" if (r.citation_ok and r.fallback_ok) else "❌"
        detail.add_row(
            r.question_id,
            r.question[:38] + ("…" if len(r.question) > 38 else ""),
            f"{r.confidence:.2f}",
            "yes" if r.is_fallback else "no",
            "yes" if r.has_citations else "no",
            f"{r.groundedness_score*100:.0f}%",
            ok,
        )

    console.print(detail)


@click.command()
@click.option("--questions-file", default=str(QUESTIONS_FILE), help="JSON file with eval questions")
@click.option("--output", default=None, help="Save results to JSON file")
@click.option("--delay", default=1.0, help="Seconds between questions (rate limiting)")
@click.option("--subset", default=None, type=int, help="Run only first N questions")
def main(questions_file: str, output: str | None, delay: float, subset: int | None):
    """Run the Ask Chipathon evaluation harness."""
    with open(questions_file, encoding="utf-8") as f:
        questions = json.load(f)

    if subset:
        questions = questions[:subset]
        console.print(f"[yellow]Running subset of {subset} questions[/yellow]")

    console.print(f"[cyan]Loaded {len(questions)} questions from {questions_file}[/cyan]\n")

    report = run_eval(questions, delay_s=delay)
    print_report(report)

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            # Convert dataclass to JSON-serializable dict
            report_dict = asdict(report)
            json.dump(report_dict, f, indent=2)
        console.print(f"\n[green]Results saved to {out_path}[/green]")


if __name__ == "__main__":
    main()
