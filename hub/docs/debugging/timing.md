# Resolving Timing (Setup & Hold) Failures

OpenROAD Flow Scripts automatically attempt to repair timing post-placement and post-CTS. However, violating paths will still occur and require manual debugging.

## Checking Timing Constraints
```tcl
report_worst_slack
report_tns
report_wns
report_checks -fields input -digits 3
```

## Setup Optimization
Setup time optimization is based on the slow corner or the best case when the launch clock arrives later than the data clock.
The `repair_design` command inserts buffers on nets to repair max slew, max capacitance and max fanout violations and on long wires to reduce RC delay. It also resizes gates to normalize slews. 

Use `estimate_parasitics -placement` before `repair_design`.

```tcl
repair_timing -setup
```
If you encounter `[WARNING RSZ-0062] Unable to repair all setup violations`, you may need to reduce the clock frequency by increasing the clock period in the `.sdc` and re-running.

## Hold Optimization
Hold time optimization is based on the fast corner or the best case when the launch clock arrives earlier than the capture clock. To fix hold violations, use `repair_timing -hold`.

While repairing hold violations, buffers are not inserted to avoid causing setup violations unless `-allow_setup_violations` is specified. OpenROAD supports multiple corner analysis to calculate worst-case setup and hold violations simultaneously.
