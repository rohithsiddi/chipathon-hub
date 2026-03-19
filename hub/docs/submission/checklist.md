# Final Submission Checklist

Before submitting your final tarball or repository link to the Chipathon organizers, ensure you have completed the following steps:

- [ ] **Timing Clean**: `report_worst_slack` for both `-min` and `-max` returns positive numbers.
- [ ] **DRC Clean**: `5_route_drc.rpt` shows 0 violations.
- [ ] **Antenna Clean**: `check_antennas` shows `violation count = 0`.
- [ ] **LVS Clean**: The layout matches the schematic (verified post-extraction).
- [ ] **GDSII Generated**: The `6_final.gds` file successfully generated and opens in KLayout without errors.
- [ ] **Metrics Generated**: `metrics.json` is populated and accurately reflects your log files.
- [ ] **Repository State**: `config.mk` and `constraint.sdc` are checked into version control.

## 24-Hour Turnaround Target
The IDEA program targets no-human-in-loop (NHIL) design. Try to minimize manual patches in your flow; relying on fully reproducible `make DESIGN_CONFIG=...` invocations is heavily preferred.
