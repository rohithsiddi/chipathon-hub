"""
chatbot/ingest/scraper.py

Fetches content from OpenROAD sources:
  1. OpenROAD ReadTheDocs site (HTTP scrape)
  2. OpenROAD-flow-scripts GitHub repo (markdown files via GitHub API)
  3. OpenROAD GitHub Issues (answered/closed)
  4. OpenROAD GitHub Discussions

Run directly:
    python -m chatbot.ingest.scraper
    chipathon-ingest       # if installed via uv pip install -e .
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import click
import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from github import Github, GithubException
from markdownify import markdownify
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

load_dotenv()

console = Console()

# ── Configuration ─────────────────────────────────────────────────────────────

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
# Treat placeholder value as unset
if GITHUB_TOKEN in ("your_github_token_here", "placeholder", ""):
    GITHUB_TOKEN = ""
RAW_DATA_DIR = Path(os.getenv("RAW_DATA_DIR", "data/raw"))

SOURCES = {
    "orfs_repo": "The-OpenROAD-Project/OpenROAD-flow-scripts",
    "openroad_repo": "The-OpenROAD-Project/OpenROAD",
}

# RTD pages to scrape
RTD_PAGES = [
    "https://openroad.readthedocs.io/en/latest/",
    "https://openroad.readthedocs.io/en/latest/user/FAQS.html",
    "https://openroad.readthedocs.io/en/latest/user/MessagesFunctions.html",
    "https://openroad-flow-scripts.readthedocs.io/en/latest/",
    "https://openroad-flow-scripts.readthedocs.io/en/latest/user/BuildLocally.html",
    "https://openroad-flow-scripts.readthedocs.io/en/latest/tutorials/FlowTutorial.html",
]

# GitHub repo paths to fetch markdown from
ORFS_MARKDOWN_PATHS = [
    "README.md",
    "flow/README.md",
    "flow/tutorials/",
    "docs/",
]

# Issue/discussion limits (keep reasonable for PoC)
MAX_ISSUES = 100
MAX_DISCUSSIONS = 50


@dataclass
class Document:
    """A single fetched document with metadata."""
    content: str
    source_url: str
    title: str
    doc_type: str  # "rtd", "github_issue", "github_discussion", "github_markdown"
    metadata: dict = field(default_factory=dict)


# ── Scrapers ──────────────────────────────────────────────────────────────────

def scrape_rtd_page(url: str, client: httpx.Client) -> Document | None:
    """Scrape a ReadTheDocs page and convert HTML to markdown."""
    try:
        resp = client.get(url, timeout=15)
        resp.raise_for_status()
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        console.print(f"[yellow]Warning: Failed to fetch {url}: {e}[/yellow]")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Extract main content — RTD uses .document or article elements
    main = soup.find("div", {"role": "main"}) or soup.find("article") or soup.find("body")
    if not main:
        return None

    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else url

    md_content = markdownify(str(main), heading_style="ATX", strip=["script", "style"])

    return Document(
        content=md_content,
        source_url=url,
        title=title,
        doc_type="rtd",
        metadata={"site": "readthedocs"},
    )


def fetch_github_markdown(gh: Github, repo_name: str, path: str) -> Iterator[Document]:
    """Fetch markdown files from a GitHub repo path."""
    try:
        repo = gh.get_repo(repo_name)
    except GithubException as e:
        console.print(f"[yellow]Warning: Cannot access repo {repo_name}: {e}[/yellow]")
        return
    try:
        contents = repo.get_contents(path)
    except GithubException as e:
        console.print(f"[yellow]Warning: Cannot access {repo_name}/{path}: {e}[/yellow]")
        return

    # Handle both files and directories
    if isinstance(contents, list):
        for item in contents:
            if item.type == "file" and item.name.endswith(".md"):
                yield from fetch_github_markdown(gh, repo_name, item.path)
            elif item.type == "dir":
                yield from fetch_github_markdown(gh, repo_name, item.path)
    else:
        item = contents
        if not item.name.endswith(".md"):
            return
        try:
            content = item.decoded_content.decode("utf-8")
            yield Document(
                content=content,
                source_url=item.html_url,
                title=item.name.replace(".md", "").replace("-", " ").replace("_", " ").title(),
                doc_type="github_markdown",
                metadata={
                    "repo": repo_name,
                    "path": item.path,
                    "sha": item.sha,
                },
            )
        except Exception as e:
            console.print(f"[yellow]Warning: Could not decode {item.path}: {e}[/yellow]")


def fetch_github_issues(gh: Github, repo_name: str, max_issues: int) -> Iterator[Document]:
    """Fetch closed/answered GitHub issues (likely contain solutions)."""
    repo = gh.get_repo(repo_name)
    issues = repo.get_issues(state="closed", sort="updated", direction="desc")

    count = 0
    for issue in issues:
        if issue.pull_request:
            continue  # skip PRs
        if count >= max_issues:
            break

        # Only include issues with at least one comment (likely answered)
        if issue.comments == 0:
            continue

        body = issue.body or ""
        comments_text = ""
        try:
            for comment in issue.get_comments():
                comments_text += f"\n\n**Comment by @{comment.user.login}:**\n{comment.body}"
        except GithubException:
            pass

        content = f"# Issue: {issue.title}\n\n{body}{comments_text}"

        yield Document(
            content=content,
            source_url=issue.html_url,
            title=issue.title,
            doc_type="github_issue",
            metadata={
                "repo": repo_name,
                "issue_number": issue.number,
                "labels": [l.name for l in issue.labels],
                "state": issue.state,
            },
        )
        count += 1
        time.sleep(0.1)  # gentle rate limiting


def fetch_github_discussions(gh: Github, repo_name: str, max_discussions: int) -> Iterator[Document]:
    """Fetch GitHub Discussions via GraphQL API."""
    if not GITHUB_TOKEN:
        console.print("[yellow]GITHUB_TOKEN not set — skipping Discussions[/yellow]")
        return

    query = """
    query($owner: String!, $repo: String!, $cursor: String) {
      repository(owner: $owner, name: $repo) {
        discussions(first: 50, after: $cursor, orderBy: {field: UPDATED_AT, direction: DESC}) {
          nodes {
            title body url
            comments(first: 5) {
              nodes { body author { login } }
            }
          }
          pageInfo { hasNextPage endCursor }
        }
      }
    }
    """
    owner, repo = repo_name.split("/")
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    cursor = None
    count = 0

    with httpx.Client() as client:
        while count < max_discussions:
            variables = {"owner": owner, "repo": repo, "cursor": cursor}
            try:
                resp = client.post(
                    "https://api.github.com/graphql",
                    json={"query": query, "variables": variables},
                    headers=headers,
                    timeout=20,
                )
                data = resp.json()
            except Exception as e:
                console.print(f"[yellow]Warning: GraphQL request failed: {e}[/yellow]")
                break

            discussions = data.get("data", {}).get("repository", {}).get("discussions", {})
            nodes = discussions.get("nodes", [])

            for node in nodes:
                if count >= max_discussions:
                    break
                body = node.get("body", "")
                comments = "\n\n".join(
                    f"**@{c['author']['login']}:** {c['body']}"
                    for c in node.get("comments", {}).get("nodes", [])
                )
                content = f"# Discussion: {node['title']}\n\n{body}"
                if comments:
                    content += f"\n\n## Replies\n{comments}"

                yield Document(
                    content=content,
                    source_url=node["url"],
                    title=node["title"],
                    doc_type="github_discussion",
                    metadata={"repo": repo_name},
                )
                count += 1

            page_info = discussions.get("pageInfo", {})
            if not page_info.get("hasNextPage"):
                break
            cursor = page_info.get("endCursor")


# ── Persistence ───────────────────────────────────────────────────────────────

def save_document(doc: Document, output_dir: Path) -> Path:
    """Save a document to disk as a JSONL entry."""
    type_dir = output_dir / doc.doc_type
    type_dir.mkdir(parents=True, exist_ok=True)

    # Use a safe filename
    safe_title = "".join(c if c.isalnum() or c in "-_ " else "_" for c in doc.title)[:80]
    filepath = type_dir / f"{safe_title}.json"

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(
            {
                "content": doc.content,
                "source_url": doc.source_url,
                "title": doc.title,
                "doc_type": doc.doc_type,
                "metadata": doc.metadata,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    return filepath


# ── Main Entry ────────────────────────────────────────────────────────────────

@click.command()
@click.option("--output-dir", default=str(RAW_DATA_DIR), help="Directory to save raw documents")
@click.option("--skip-rtd", is_flag=True, default=False, help="Skip ReadTheDocs scraping")
@click.option("--skip-github", is_flag=True, default=False, help="Skip GitHub content fetching")
@click.option("--max-issues", default=MAX_ISSUES, help="Max issues to fetch per repo")
def main(output_dir: str, skip_rtd: bool, skip_github: bool, max_issues: int):
    """Fetch and save all Chipathon/OpenROAD knowledge base documents."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    console.rule("[bold blue]Chipathon Ingest Pipeline[/bold blue]")
    total_saved = 0

    # ── 1. Scrape ReadTheDocs ──
    if not skip_rtd:
        console.print("\n[cyan]📚 Scraping ReadTheDocs pages...[/cyan]")
        with httpx.Client(follow_redirects=True) as client:
            with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
                task = progress.add_task("Scraping RTD...", total=len(RTD_PAGES))
                for url in RTD_PAGES:
                    progress.update(task, description=f"Scraping: {url[-50:]}")
                    doc = scrape_rtd_page(url, client)
                    if doc:
                        save_document(doc, out_dir)
                        total_saved += 1
                    progress.advance(task)

    # ── 2. Fetch GitHub content ──
    if not skip_github:
        if GITHUB_TOKEN:
            console.print(f"[green]✓ Using authenticated GitHub API (5000 req/hr)[/green]")
            gh = Github(GITHUB_TOKEN)
        else:
            console.print("[yellow]⚠️  No GITHUB_TOKEN — using unauthenticated API (60 req/hr). Set GITHUB_TOKEN in .env for faster fetching.[/yellow]")
            gh = Github()

        with Progress(
            SpinnerColumn(), TextColumn("{task.description}"),
            BarColumn(), TaskProgressColumn(), console=console
        ) as progress:

            # ORFS markdown files
            console.print("\n[cyan]📦 Fetching ORFS markdown files...[/cyan]")
            for path in ORFS_MARKDOWN_PATHS:
                task = progress.add_task(f"ORFS: {path}", total=None)
                for doc in fetch_github_markdown(gh, SOURCES["orfs_repo"], path):
                    save_document(doc, out_dir)
                    total_saved += 1
                progress.remove_task(task)

            # OpenROAD issues
            console.print("\n[cyan]🐛 Fetching OpenROAD GitHub Issues...[/cyan]")
            task = progress.add_task("Issues...", total=max_issues)
            for doc in fetch_github_issues(gh, SOURCES["openroad_repo"], max_issues):
                save_document(doc, out_dir)
                total_saved += 1
                progress.advance(task)
            progress.remove_task(task)

            # OpenROAD discussions
            console.print("\n[cyan]💬 Fetching OpenROAD GitHub Discussions...[/cyan]")
            task = progress.add_task("Discussions...", total=MAX_DISCUSSIONS)
            for doc in fetch_github_discussions(gh, SOURCES["openroad_repo"], MAX_DISCUSSIONS):
                save_document(doc, out_dir)
                total_saved += 1
                progress.advance(task)
            progress.remove_task(task)

    console.rule()
    console.print(f"[green]✅ Saved {total_saved} documents to {out_dir}[/green]")
    console.print("\nNext step: [bold]python -m chatbot.ingest.chunker[/bold]")


if __name__ == "__main__":
    main()
