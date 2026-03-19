# Tagging Canonical GitHub Issues

The "Ask Chipathon" AI bot parses the official OpenROAD GitHub repositories for tacit technical knowledge.

To prevent the AI from ingesting terrible advice or noisy threads, it filters GitHub API queries.

## How to flag a thread for the AI:

If a student posts an issue on `The-OpenROAD-Project/OpenROAD` or `The-OpenROAD-Project/OpenROAD-flow-scripts` and the core engineering team provides a definitive, correct answer:

1. Ensure the issue state is marked as **Closed** (the AI ignores open, unresolved issues).
2. Ensure the GitHub label `chipathon-canonical` or `bug` is applied.
3. Upvote the correct comment with a 👍 reaction.

The `scraper.py` script prioritizes the highest upvoted comments in resolved threads containing these labels to build its text embeddings.
