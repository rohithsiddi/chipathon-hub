# Track 1: Standard Digital Flow

This document describes the basics to run the complete OpenROAD flow from RTL-to-GDS using OpenROAD Flow Scripts. 

## Initializing a Design
Sample design configurations are available in the `designs` directory of ORFS.
You can specify the design using the shell environment. For example:

```shell
# Make sure you are in ./flow
make DESIGN_CONFIG=./designs/nangate45/swerv/config.mk
# or
export DESIGN_CONFIG=./designs/nangate45/swerv/config.mk
make
```

By default, the `gcd` design is selected using the `nangate45` platform. The resulting GDS will be available at `flow/results/nangate45/gcd/6_final.gds`. This design takes only a few minutes.

## Important Flow Variables
The following design-specific configuration variables are required in your `config.mk` to specify main design inputs:

| Variable Name | Description |
|---|---|
| `PLATFORM` | Specifies Process design kit (e.g. `sky130hd`). |
| `DESIGN_NAME` | The name of the top-level module of the design. |
| `VERILOG_FILES` | The path to the design Verilog files or JSON files. |
| `SDC_FILE` | The path to design `.sdc` file. |
| `CORE_UTILIZATION` | The core utilization percentage. |
| `PLACE_DENSITY` | The desired placement density of cells (1 = closely dense, 0 = widely spread). |

## Cleaning Previous Runs
OpenROAD-flow-scripts can generally restart from a previous partial run. If you have errors which prevent restarting the flow, you may try deleting all generated files:

```shell
make clean_all DESIGN_CONFIG=./designs/sky130hd/ibex/config.mk
```
You can also delete files related to individual stages with `clean_synth`, `clean_floorplan`, `clean_place`, `clean_cts`, `clean_route`, and `clean_finish`.
