"""
Fetches content from OpenROAD sources:
  1. OpenROAD ReadTheDocs pages
  2. ORFS GitHub repo markdown files
  3. OpenROAD GitHub Issues (closed, with comments)
  4. OpenROAD GitHub Discussions

Run: python -m chatbot.ingest.scraper
"""

from __future__ import annotations

import json
import os
import re
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

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
if GITHUB_TOKEN in ("your_github_token_here", "placeholder", ""):
    GITHUB_TOKEN = ""

RAW_DATA_DIR = Path(os.getenv("RAW_DATA_DIR", "data/raw"))

SOURCES = {
    "orfs_repo": "The-OpenROAD-Project/OpenROAD-flow-scripts",
    "openroad_repo": "The-OpenROAD-Project/OpenROAD",
}

RTD_PAGES = [
    "https://openroad.readthedocs.io/en/latest/",
    "https://openroad.readthedocs.io/en/latest/user/FAQS.html",
    "https://openroad.readthedocs.io/en/latest/user/MessagesFunctions.html",
    "https://openroad-flow-scripts.readthedocs.io/en/latest/",
    "https://openroad-flow-scripts.readthedocs.io/en/latest/user/BuildLocally.html",
    "https://openroad-flow-scripts.readthedocs.io/en/latest/tutorials/FlowTutorial.html",
]

ORFS_MARKDOWN_PATHS = [
    "README.md",
    "flow/README.md",
    "flow/tutorials/",
    "docs/",
]

MAX_ISSUES = 100
MAX_DISCUSSIONS = 50
MAX_COMMENTS_PER_ISSUE = 10
MIN_ISSUE_BODY_CHARS = 50


@dataclass
class Document:
    content: str
    source_url: str
    title: str
    doc_type: str  # "rtd", "github_issue", "github_discussion", "github_markdown"
    metadata: dict = field(default_factory=dict)


def clean_markdown(text: str) -> str:
    """Remove common scraping artifacts from markdownified RTD content."""
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'\s*\[¶\]\([^)]+\)', '', text)
    text = re.sub(r'\s*¶', '', text)
    text = re.sub(r'\[(?:Edit|View source?)[^\]]*\]\([^)]+\)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[\]\([^)]*\)', '', text)
    text = re.sub(r'\n\s*\[(?:next|previous|index|contents)\][^\n]*', '', text, flags=re.IGNORECASE)
    return text.strip()


def scrape_rtd_page(url: str, client: httpx.Client) -> Document | None:
    try:
        resp = client.get(url, timeout=15)
        resp.raise_for_status()
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        console.print(f"[yellow]Warning: Failed to fetch {url}: {e}[/yellow]")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    main = soup.find("div", {"role": "main"}) or soup.find("article") or soup.find("body")
    if not main:
        return None

    # Strip navigation and UI chrome — these are pure noise in embeddings
    for tag in main.find_all(["nav", "script", "style", "button", "footer"]):
        tag.decompose()
    for cls in ["headerlink", "toctree-wrapper", "sphinx-tabs-tab"]:
        for tag in main.find_all(class_=cls):
            tag.decompose()
    for tag in main.find_all("div", class_=re.compile(r"breadcrumb|highlight-default")):
        tag.decompose()
    for tag in main.find_all("a", string=re.compile(r"edit|source", re.IGNORECASE)):
        tag.decompose()

    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else url

    md_content = markdownify(str(main), heading_style="ATX", strip=["script", "style"])
    md_content = clean_markdown(md_content)

    return Document(
        content=md_content,
        source_url=url,
        title=title,
        doc_type="rtd",
        metadata={"site": "readthedocs"},
    )


def fetch_github_markdown(gh: Github, repo_name: str, path: str) -> Iterator[Document]:
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
                metadata={"repo": repo_name, "path": item.path, "sha": item.sha},
            )
        except Exception as e:
            console.print(f"[yellow]Warning: Could not decode {item.path}: {e}[/yellow]")


def fetch_github_issues(gh: Github, repo_name: str, max_issues: int) -> Iterator[Document]:
    """Fetch closed GitHub issues formatted as Q&A."""
    repo = gh.get_repo(repo_name)
    issues = repo.get_issues(state="closed", sort="updated", direction="desc")

    count = 0
    for issue in issues:
        if issue.pull_request:
            continue
        if count >= max_issues:
            break

        body = (issue.body or "").strip()
        if len(body) < MIN_ISSUE_BODY_CHARS or issue.comments == 0:
            continue

        labels = [lb.name for lb in issue.labels]

        comments_text = ""
        try:
            for i, comment in enumerate(issue.get_comments()):
                if i >= MAX_COMMENTS_PER_ISSUE:
                    break
                author = comment.user.login if comment.user else "unknown"
                comments_text += f"\n\n**@{author}:**\n{comment.body or ''}"
        except GithubException:
            pass

        label_str = ", ".join(labels) if labels else "none"
        content = (
            f"# {issue.title}\n\n"
            f"**Labels:** {label_str}\n\n"
            f"**Problem:**\n{body}\n\n"
            f"**Discussion & Resolution:**{comments_text}"
        )

        yield Document(
            content=content,
            source_url=issue.html_url,
            title=issue.title,
            doc_type="github_issue",
            metadata={
                "repo": repo_name,
                "issue_number": issue.number,
                "labels": labels,
                "state": issue.state,
            },
        )
        count += 1
        time.sleep(0.1)


def fetch_github_discussions(gh: Github, repo_name: str, max_discussions: int) -> Iterator[Document]:
    """Fetch GitHub Discussions via GraphQL."""
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


def save_document(doc: Document, output_dir: Path) -> Path:
    type_dir = output_dir / doc.doc_type
    type_dir.mkdir(parents=True, exist_ok=True)

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

    if not skip_rtd:
        console.print("\n[cyan]Scraping ReadTheDocs pages...[/cyan]")
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

    if not skip_github:
        if GITHUB_TOKEN:
            console.print(f"[green]Using authenticated GitHub API (5000 req/hr)[/green]")
            gh = Github(GITHUB_TOKEN)
        else:
            console.print("[yellow]No GITHUB_TOKEN — using unauthenticated API (60 req/hr)[/yellow]")
            gh = Github()

        with Progress(
            SpinnerColumn(), TextColumn("{task.description}"),
            BarColumn(), TaskProgressColumn(), console=console
        ) as progress:

            console.print("\n[cyan]Fetching ORFS markdown files...[/cyan]")
            for path in ORFS_MARKDOWN_PATHS:
                task = progress.add_task(f"ORFS: {path}", total=None)
                for doc in fetch_github_markdown(gh, SOURCES["orfs_repo"], path):
                    save_document(doc, out_dir)
                    total_saved += 1
                progress.remove_task(task)

            console.print("\n[cyan]Fetching OpenROAD GitHub Issues...[/cyan]")
            task = progress.add_task("Issues...", total=max_issues)
            for doc in fetch_github_issues(gh, SOURCES["openroad_repo"], max_issues):
                save_document(doc, out_dir)
                total_saved += 1
                progress.advance(task)
            progress.remove_task(task)

            console.print("\n[cyan]Fetching OpenROAD GitHub Discussions...[/cyan]")
            task = progress.add_task("Discussions...", total=MAX_DISCUSSIONS)
            for doc in fetch_github_discussions(gh, SOURCES["openroad_repo"], MAX_DISCUSSIONS):
                save_document(doc, out_dir)
                total_saved += 1
                progress.advance(task)
            progress.remove_task(task)

    console.rule()
    console.print(f"[green]Saved {total_saved} documents to {out_dir}[/green]")
    console.print("\nNext: [bold]python -m chatbot.ingest.chunker[/bold]")


if __name__ == "__main__":
    main()
