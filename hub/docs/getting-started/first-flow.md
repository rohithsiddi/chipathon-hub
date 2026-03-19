---
title: First Flow Run
description: Run your first RTL-to-GDSII flow with OpenROAD
---

# Your First Flow Run

Once inside the Docker container, run the built-in demo design:

```bash
cd /OpenROAD-flow-scripts
make DESIGN_CONFIG=./flow/designs/nangate45/gcd/config.mk
```

## Expected Outputs

| File | What it is |
|------|-----------|
| `results/.../1_1_yosys.v` | Post-synthesis Verilog |
| `results/.../3_5_route.def` | Post-routing DEF |
| `results/.../6_final.gds` | Final GDSII |
| `reports/.../metrics.json` | QoR summary |

!!! success "Success Criteria"
    If you see `[FLOW] Elapsed time: ...` without errors, your environment works.

## Run Stage by Stage

```bash
make 1_synth DESIGN_CONFIG=...    # Synthesis only
make 2_floorplan DESIGN_CONFIG=... # Floorplan only
make 5_route DESIGN_CONFIG=...    # Through routing
make 6_finish DESIGN_CONFIG=...   # Full flow
```
