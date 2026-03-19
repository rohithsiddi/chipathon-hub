# Resolving Routing & Congestion Failures

The global router analyzes available routing resources and automatically allocates them to avoid any H/V overflow violations for optimal routing. It generates a congestion report for GCells showing total resources, demand, utilization, location and the H/V violation status.

## Debugging Problems in Global Routing

The global router has a few useful functionalities to understand high congestion issues in the designs.
If the design has congestion issue, it ends with the error:
```
[ERROR GRT-0118] Routing congestion too high.
```

### GUI Visualization
In the OpenROAD GUI, you can go under `Heat Maps` from the Display Control window and mark the `Routing Congestion` checkbox to visualize the congestion map. 

### Dumping Congestion Details
You can create a text file with the congestion information of the GCells for further investigation on the GUI. Add `-congestion_report_file` to the global route command:
```tcl
global_route -guide_file out.guide -congestion_report_file congest.rpt
```
Load this file into the `DRC Viewer` in the GUI. The viewer will place markers on overflowing GCells, allowing you to use the `Inspector` window to see total resources and utilization.

## Detailed Routing Debugging

The following command and arguments are useful when debugging error messages from `drt` and to understand its behavior.

```tcl
detailed_route_debug [-pa] [-ta] [-dr] [-maze] [-net name] [-pin name] [-box x1 y1 x2 y2] 
```
- `-pa`: Enable debug for pin access
- `-ta`: Enable debug for track assignment
- `-dr`: Enable debug for detailed routing
- `-maze`: Enable debug for maze routing 
- `-net`: Enable debug for a specific net name

For successful routing, DRT will end with `Number of violations = 0`.
