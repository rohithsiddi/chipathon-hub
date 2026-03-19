# Maintainer Contributor Guide

The primary goal of the "Ask Chipathon" framework is to make knowledge ingestion seamless for mentors.

## Adding Content to the Hub

If you see a student struggling with a novel problem on Discord, and you discover the fix:

1. Create a quick markdown file explaining the fix.
2. Submit a PR to this `chipathon-hub` repository.
3. Once merged to `main`, the GitHub Action `.github/workflows/rebuild-index.yml` will automatically rebuild the static site.

### The AI Advantage

You do **not** need to manually update the RAG chatbot database! Since `scraper.py` is configured to pull down this entire MkDocs site as part of its ingestion run, simply writing documentation automatically makes the AI smarter.

## Formatting Guidelines
- Use **Mermaid.js** flowcharts for debugging.
- Highlight specific keywords (like `CLOCK_PERIOD`) with backticks.
- If providing a configuration override, place it inside a ````makefile` code block.
