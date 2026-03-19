---
title: Artifact Map
description: Where to find every log, report, DEF, GDS file and how to interpret OpenROAD outputs
---

# Chipathon Artifact Map

After each flow stage, OpenROAD-flow-scripts deposits files in predictable locations. This map tells you exactly where to look and what each file means.

## Directory Structure

```
flow/
├── designs/<pdk>/<design>/
│   └── config.mk               ← Your design configuration
│
├── logs/<pdk>/<design>/        ← Per-stage logs (start here when debugging)
│   ├── 1_1_yosys.log
│   ├── 2_1_floorplan.log
│   ├── 3_1_place.log
│   ├── 4_1_cts.log
│   ├── 5_1_grt.log
│   ├── 5_3_route.log
│   └── 6_report.log
│
├── reports/<pdk>/<design>/     ← QoR reports
│   ├── 6_final_report.rpt      ← ⭐ Primary timing report
│   ├── 6_drc.rpt               ← DRC violation count + details
│   ├── 6_power.rpt             ← Power breakdown
│   └── metrics.json            ← Machine-readable QoR summary
│
└── results/<pdk>/<design>/     ← Physical artifacts
    ├── 1_1_yosys.v             ← Post-synthesis Verilog netlist
    ├── 2_floorplan.def         ← Floorplan DEF
    ├── 3_5_route.def           ← Post-route DEF (pre-final)
    ├── 5_route.odb             ← OpenDB database (all stages)
    ├── 6_final.def             ← Final DEF
    ├── 6_final.gds             ← ⭐ Final GDSII (your submission artifact)
    └── 6_final.spef            ← Parasitic extraction
```

---

## Key Files Explained

### `metrics.json` — Your QoR Dashboard

```json
{
  "finish__design__instance__count__stdcell": 1234,
  "finish__timing__setup__ws": -0.012,     // WNS — should be ≥ 0
  "finish__timing__setup__tns": -1.5,      // TNS — should be 0
  "finish__power__total": 0.00234,
  "finish__design__instance__area": 45678,
  "finish__route__drc_errors": 0           // Must be 0 for submission
}
```

!!! success "Submission-Ready Criteria"
    - `finish__route__drc_errors` == `0`
    - `finish__timing__setup__ws` >= `0` (positive slack)

### `6_final_report.rpt` — Timing Report

```
Worst Slack (setup):   0.123 ns    ← Positive = passing
Total Negative Slack:  0.000 ns    ← Zero = no violations
No timing paths violate constraint
```

### `6_drc.rpt` — DRC Report

```
[DRC] Total violations: 0          ← Target: 0
  metal1_spacing: 0
  via1_enclosure: 0
```

---

## Submission Artifacts Checklist

| Artifact | Location | Required |
|----------|----------|----------|
| Final GDS | `results/.../6_final.gds` | ✅ Yes |
| Final DEF | `results/.../6_final.def` | ✅ Yes |
| Timing report | `reports/.../6_final_report.rpt` | ✅ Yes |
| DRC report (0 violations) | `reports/.../6_drc.rpt` | ✅ Yes |
| metrics.json | `reports/.../metrics.json` | ✅ Yes |
| Power report | `reports/.../6_power.rpt` | Recommended |
| SPEF | `results/.../6_final.spef` | Track-dependent |

!!! warning "Before Submitting"
    Run `make drc` explicitly even if the flow reported 0 DRC — some PDK rules are only checked in the standalone DRC step.

---

## Viewing Your GDS

```bash
# Using KLayout (free, open source)
klayout flow/results/<pdk>/<design>/6_final.gds

# Quick DRC check in KLayout
klayout -b -r <pdk_drc_script>.lydrc flow/results/.../6_final.gds
```
