---
title: Debugging Playbooks
description: Recipes for fixing timing, DRC, routing, and environment failures in OpenROAD
---

# Debugging Playbooks

Use this section when something goes wrong. Each playbook follows the same structure: **symptoms → root causes → fix steps → how to verify**.

---

## Timing Failures

### Symptoms

- `[STA] VIOLATED` in the log
- Negative WNS/TNS in `reports/6_final_report.rpt`
- Message: `setup time violation`

### Common Root Causes

| Cause | Indicator |
|-------|-----------|
| Clock period too tight | WNS close to `-clock_period` |
| Long combinational path | Largest endpoint slack in timing report |
| Missing false paths | Paths across clock domains flagged |
| Unoptimized synthesis | High fanout nets in netlist |

### Fix Steps

```bash
# 1. Find the worst offending path
openroad -exit << 'EOF'
read_db flow/results/<pdk>/<design>/5_route.odb
report_worst_slack -digits 3
report_timing -path_delay max -endpoint_count 10
EOF

# 2. Relax clock: increase CLOCK_PERIOD in config.mk
#    (start with +0.2 ns increments)
sed -i 's/^export CLOCK_PERIOD = .*/export CLOCK_PERIOD = 2.2/' flow/designs/.../config.mk

# 3. Enable post-placement optimization
# In config.mk:
# export GPL_ROUTABILITY_DRIVEN = 1
# export DPO_MAX_DISPLACEMENT = 5 5
```

!!! tip "Timing Report Location"
    `flow/results/<pdk>/<design>/reports/6_final_report.rpt`

---

## DRC Violations

### Symptoms

- Non-zero DRC count at the end of the flow
- `KLayout` showing red markers on the GDS
- Message: `[DRC] X violations found`

### Common Root Causes

| Violation Type | Likely Cause |
|---------------|--------------|
| `min_spacing` | Routing track density too high |
| `min_width` | Non-default routing rule applied incorrectly |
| `via_enclosure` | Via generation settings for the PDK |
| `antenna` | Long metal routes without antenna diodes |

### Fix Steps

```bash
# View DRC report
cat flow/results/<pdk>/<design>/reports/6_drc.rpt

# Fix antenna violations: enable antenna repair in config.mk
echo 'export ANTENNA_REPAIR = 1' >> flow/designs/.../config.mk

# For persistent min_spacing: reduce routing target density
echo 'export ROUTING_TARGET_DENSITY = 0.60' >> flow/designs/.../config.mk

make DESIGN_CONFIG=... clean_drt  # re-run only detailed routing
```

!!! warning "Never Skip DRC"
    Submissions with DRC violations will be disqualified. Always run `make drc` before submitting.

---

## Routing Failures

### Symptoms

- `[ERROR DRT-0305]` or routing congestion messages
- Flow terminates at `5_3_route` stage
- `routing_overflow` in metrics

### Fix Steps

```bash
# 1. Check congestion map
openroad -exit << 'EOF'
read_db flow/results/<pdk>/<design>/4_cts.odb
detailed_route_debug    # generates congestion heatmap
EOF

# 2. Reduce utilization in config.mk
# export CORE_UTILIZATION = 40   (try lower values, e.g. 35)
# export CORE_ASPECT_RATIO = 1
# export CORE_MARGIN = 2

# 3. Enable global route driven placement
# export GPL_ROUTABILITY_DRIVEN = 1
```

---

## Environment Issues

### Docker Permission Errors

```bash
# Add your user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker

# Or run with sudo (temporary fix only)
sudo docker run ...
```

### `make: command not found`

```bash
# Ubuntu/Debian
sudo apt-get install build-essential

# macOS
xcode-select --install
```

### Flow Hangs / OOM

```bash
# Limit parallel jobs if running low on RAM
make -j2 DESIGN_CONFIG=...

# Monitor memory
htop  # or: watch -n1 free -h
```

!!! info "Getting More Help"
    Paste the **last 30 lines of your log** when asking for help — not just the error. Use `tail -30 flow/logs/<stage>.log`
