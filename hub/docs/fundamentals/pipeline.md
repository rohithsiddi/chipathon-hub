# RTL-to-GDS Pipeline

The OpenROAD application executes the entire autonomous flow using Tcl scripts that invoke open-sourced tools, from synthesis to the final `.gds` file creation, without requiring human intervention.

## Core Flow Stages
From the OpenROAD-flow-scripts directory, users can access individual flow stages and respective tools:

- `1_1_yosys`: Synthesis using Yosys
- `2_floorplan`: Initialization based on Core and Die Area, inserting Tap Cells.
- `3_place`: Global placement, Macro placement with Halo Spacing
- `4_cts`: Clock Tree Synthesis and Balancing
- `5_route`: Global Routing (GRT) and Detailed Routing (DRT/TritonRoute)
- `6_final`: Metadata, Fill, and Output Layout Generation (KLayout)

## Power & Verification
Pdngen is used for power planning. PDNSim is an open-source static IR analyzer used to report worst IR drop and current density over the power network.

## Exploring Results
`make gui_final` command target successively reads and loads the technology `.odb` files and the parasitics (`.spef`) to invoke the OpenROAD GUI.

Use the `Tcl Commands` section to run reports:
```tcl
report_design_area
report_power
report_worst_slack
```

The GUI allows users to select, control, highlight and navigate the design hierarchy and design objects (nets, pins, instances, paths) through detailed visualization.
