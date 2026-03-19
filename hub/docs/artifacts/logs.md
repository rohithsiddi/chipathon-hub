# Where are my logs?

OpenROAD-flow-scripts prepends a prefix to each flow stage to indicate the position in the RTL-GDS flow. This makes it easier to understand and debug each flow stage in case of failure.

Logs are located in `flow/logs/<platform>/<design>/base/`

## Standard Log Structure
| File Name | Description |
|-----------|-------------|
| `1_1_yosys.log` | Synthesis results. Check for missing module warnings. |
| `2_floorplan.log` | Core and die area initialization logs. |
| `3_place.log` | Global and detailed placement. Look for density issues here. |
| `4_cts.log` | Clock tree synthesis skew reports. |
| `5_1_grt.log` | Global routing congestion maps (`[INFO GRT-0096]`). |
| `5_2_route.log` | TritonRoute detailed routing logs (`[INFO DRT-0199]`). |

## Checking Errors
If a stage fails, always look at the bottom of the corresponding log file. OpenROAD usually prefixes fatal errors with `[ERROR XYZ-####]`. 
