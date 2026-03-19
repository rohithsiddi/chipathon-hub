---
title: RTL to GDSII Overview
description: High-level overview of the full chip design flow from RTL to GDSII
---

# RTL to GDSII Overview

The complete journey from RTL description to a manufacturable layout (GDSII) goes through these major milestones:

## 1 — Synthesis
**Tool:** Yosys  
**Input:** RTL Verilog  
**Output:** `1_1_yosys.v` — gate-level netlist using standard cells from your PDK

```bash
# Run just synthesis
make 1_synth DESIGN_CONFIG=./flow/designs/<pdk>/<design>/config.mk
```

## 2 — Floorplan
**Tool:** OpenROAD  
**Output:** `2_floorplan.def` — die area, IO placement, power rings

## 3 — Placement
**Tool:** OpenROAD (RePlAce / DPL)  
**Output:** `3_5_route.def` — all cells placed within the core area

## 4 — Clock Tree Synthesis (CTS)
**Tool:** OpenROAD (TritonCTS)  
**Output:** Balanced clock trees inserted into the design

## 5 — Routing
**Tool:** OpenROAD (FastRoute + TritonRoute)  
**Output:** `5_route.odb` — all nets routed on metal layers

## 6 — Finishing
**Tools:** KLayout / Magic  
**Output:** `6_final.gds` — DRC-checked, ready for submission
