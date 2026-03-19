---
title: Chipathon Knowledge Hub
description: Central guide for IEEE SSCS Chipathon participants using OpenROAD-based flows
---

<div class="chipathon-hero">
  <h1>Chipathon Knowledge Hub</h1>
  <p>Your central guide for IEEE SSCS Chipathon — from environment setup to GDSII submission.<br>
  Powered by the OpenROAD open-source EDA flow.</p>
</div>

## Quick Navigation

<div class="cards-grid">
  <a class="card" href="getting-started/">
    <div class="card-icon">🚀</div>
    <h3>Getting Started</h3>
    <p>Environment setup, tool versions, and your first flow run</p>
  </a>
  <a class="card" href="openroad-flow/">
    <div class="card-icon">⚙️</div>
    <h3>OpenROAD Flow</h3>
    <p>RTL to GDSII stages, configuration, and flow fundamentals</p>
  </a>
  <a class="card" href="debugging/">
    <div class="card-icon">🔍</div>
    <h3>Debugging Playbooks</h3>
    <p>Timing, DRC, routing, and environment failure recipes</p>
  </a>
  <a class="card" href="artifact-map/">
    <div class="card-icon">🗺️</div>
    <h3>Artifact Map</h3>
    <p>Where to find logs, DEF, GDS, metrics — and how to read them</p>
  </a>
  <a class="card" href="faq/">
    <div class="card-icon">❓</div>
    <h3>FAQ</h3>
    <p>Canonical answers to the most common Chipathon questions</p>
  </a>
  <a class="card" href="chatbot/">
    <div class="card-icon">🤖</div>
    <h3>Ask Chipathon</h3>
    <p>AI chatbot with citations — ask anything about the flow</p>
  </a>
</div>

---

## About This Hub

The [IEEE SSCS Chipathon](https://sscs.ieee.org/chipathon) brings together teams going from RTL to GDSII using [OpenROAD-based flows](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts). During the competition, participants repeatedly hit the same hurdles — environment setup, version mismatches, flow configuration, log interpretation, and debugging failures.

**This hub centralizes those answers** so you can self-serve instead of waiting on mentors, with all content sourced directly from canonical OpenROAD repositories and past Chipathon guidance.

!!! tip "Can't find what you need?"
    Try the [Ask Chipathon chatbot →](chatbot.md) — it retrieves answers with citations to exact doc sections and GitHub threads.

---

## Frequently Hit Issues (Quick Links)

| Problem | Guide |
|---------|-------|
| Docker setup fails | [Environment Setup → Docker](getting-started/environment-setup.md#docker) |
| Synthesis fails with Yosys error | [Debugging → Environment](debugging/environment.md) |
| Setup timing violations | [Debugging → Timing](debugging/timing.md) |
| DRC errors won't clear | [Debugging → DRC](debugging/drc.md) |
| Routing fails with congestion | [Debugging → Routing](debugging/routing.md) |
| Where are my GDS/reports? | [Artifact Map](artifact-map.md) |
