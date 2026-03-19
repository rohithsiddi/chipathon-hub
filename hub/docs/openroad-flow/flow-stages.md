---
title: Flow Stages
description: Detailed description of each ORFS flow stage and its make targets
---

# Flow Stages

## Make Targets

Each stage has a corresponding `make` target you can run individually:

| Stage | Target | Output Dir |
|-------|--------|-----------|
| Synthesis | `1_synth` | `results/.../1_*.v` |
| Floorplan | `2_floorplan` | `results/.../2_*.def` |
| Placement | `3_place` | `results/.../3_*.def` |
| CTS | `4_cts` | `results/.../4_*.def` |
| Global routing | `5_1_grt` | `results/.../5_*.def` |
| Detailed routing | `5_3_route` | `results/.../5_route.odb` |
| Finishing | `6_finish` | `results/.../6_final.gds` |

## Re-running a Single Stage

```bash
# Re-run only detailed routing
make clean_drt DESIGN_CONFIG=...
make 5_3_route DESIGN_CONFIG=...
```

## Logs

All logs are in `flow/logs/<pdk>/<design>/`:
```
1_1_yosys.log
2_1_floorplan.log
3_1_place.log
4_1_cts.log
5_1_grt.log
5_3_route.log
6_report.log
```
