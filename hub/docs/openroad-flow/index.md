---
title: OpenROAD Flow
description: Overview of the OpenROAD RTL-to-GDSII flow
---

# OpenROAD Flow

## What is ORFS?

OpenROAD-flow-scripts (ORFS) is a fully automated RTL-to-GDSII flow built on the OpenROAD toolchain. It orchestrates synthesis, floor planning, placement, CTS, routing, and finishing into a single `make` command.

## Flow Stages

```
RTL (Verilog)
    ↓  Synthesis (Yosys)
Gate-level Netlist
    ↓  Floorplan (OpenROAD)
Floorplan DEF
    ↓  Placement (OpenROAD)
Placed DEF
    ↓  CTS (OpenROAD)
Clock-Tree DEF
    ↓  Global Routing (OpenROAD)
    ↓  Detailed Routing (OpenROAD)
Routed DEF
    ↓  Finishing (KLayout / Magic)
Final GDS
```

See the sub-pages for in-depth documentation on each stage.
