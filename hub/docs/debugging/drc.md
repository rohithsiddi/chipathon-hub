# Resolving DRC & LVS Failures

In the OpenROAD flow, any DRC violations are logged in the `5_route_drc.rpt` file.

```shell
less ./reports/sky130hd/ibex/base/5_route_drc.rpt
```

## Using the DRC Viewer

When violations occur post detail routing, the number of violations left in the design will be logged:
`[INFO DRT-0199] Number of violations = 7.`

1. Launch `openroad -gui`
2. Enable the menu options `Windows` -> `DRC Viewer`. 
3. From `DRC Viewer` -> `Load` navigate to the `5_route_drc.rpt` file.

An `X mark` in the layout designates the DRC violations. From the DRM Viewer, expand the violation hierarchy (e.g. `Short`) to see the exact instances. 
Open the input DEF file to check the source of the overlap manually if necessary (often caused by overlapping placements of clock buffers or unconstrained macro halos).

## Antenna Checker

Antenna Violation occurs when the antenna ratio exceeds a value specified in a Process Design Kit (PDK). This tool checks antenna violations and generates a report.

```tcl
check_antennas -verbose
puts "violation count = [ant::antenna_violation_count]"

# Check if net50 has a violation
set net "net50"
puts "Net $net violations: [ant::check_net_violation $net]"
```
