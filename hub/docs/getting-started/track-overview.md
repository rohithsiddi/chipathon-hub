---
title: Track Overview
description: Chipathon track options and PDK requirements
---

# Track Overview

The Chipathon typically runs multiple tracks with different PDKs and constraints.

| Track | PDK | Key Constraints |
|-------|-----|-----------------|
| Digital | Nangate45 / SKY130 | Timing closure, area |
| Mixed-Signal | SKY130 | Analog + digital integration |
| Advanced | ASAP7 | Advanced node challenges |

## Choosing Your Track

- **First-timers**: Start with the Nangate45 digital track — most tutorials target it
- **Experienced teams**: SKY130 gives you a real, open-source manufacturable PDK
- **Research focus**: ASAP7 for advanced node EDA exploration

!!! info "Check Your Track Config"
    Your track's `config.mk` defines your PDK, clock period, and die area.
    Always start from the provided template — do **not** start from scratch.
