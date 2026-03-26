---
title: Ask Chipathon
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
short_description: RAG chatbot for OpenROAD EDA flow questions
---

# Ask Chipathon API

Backend API for the Ask Chipathon chatbot — part of a GSoC 2026 proof-of-concept for the IEEE SSCS Chipathon.

**POST** `/chat` with `{"query": "your question"}` to get an answer grounded in OpenROAD documentation, GitHub issues, and community discussions.

The knowledge base covers placement, routing, clock tree synthesis, timing analysis, PDN generation, and the full ORFS flow. Answers include source citations. If confidence is low, the bot returns a structured triage response instead of guessing.

See the [knowledge hub](https://rohithsiddi.github.io/chipathon-hub/) and [source repo](https://github.com/rohithsiddi/Chipathon) for more.
