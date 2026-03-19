---
title: Flow Configuration
description: Key config.mk variables for controlling the OpenROAD flow
---

# Flow Configuration

All flow settings live in your design's `config.mk`.

## Key Variables

```makefile
# ── Design ─────────────────────────────────
export DESIGN_NAME = gcd
export PLATFORM    = nangate45

# ── Timing ─────────────────────────────────
export CLOCK_PERIOD = 2.0      # nanoseconds — start relaxed, tighten later
export CLOCK_PORT   = clk

# ── Floorplan ──────────────────────────────
export CORE_UTILIZATION  = 40  # % of core filled with cells (40-60 recommended)
export CORE_ASPECT_RATIO = 1   # height/width
export CORE_MARGIN       = 2   # margin in microns

# ── Routing ────────────────────────────────
export ROUTING_TARGET_DENSITY = 0.70  # lower = less congestion

# ── Optimization ───────────────────────────
export GPL_ROUTABILITY_DRIVEN = 1     # routability-driven placement
export ANTENNA_REPAIR         = 1     # auto fix antenna violations
```

## Useful Tuning Tips

| Problem | Variable to adjust |
|---------|-------------------|
| Timing violations | Increase `CLOCK_PERIOD` |
| Routing congestion | Decrease `ROUTING_TARGET_DENSITY` or `CORE_UTILIZATION` |
| DRC antenna errors | Enable `ANTENNA_REPAIR = 1` |
| OOM / slow runs | Reduce `-j` parallelism |
