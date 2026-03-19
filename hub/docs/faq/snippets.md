# Configuration Snippet Library

When customizing your flow for the Chipathon, `variables.mk` and `config.mk` adjustments are critical.

## Changing Routing Resources
If you are hit with `Routing congestion too high`, you can attempt to alter placement density, but you can also manually increase the routing halo around macros:

```tcl
macro_placement -halo {0.5 0.5}
```

## Creating Complex Clocks
Usually a single `create_clock` is all it takes for the RTL-to-GDS flow, but if you need to override the period:

```tcl
create_clock -name core_clock -period 17.4 [get_ports {clk_i}]
```

## Using Custom Yosys Flags
`make run-yosys` sets up all the ORFS environment variables and launches Yosys.
You can use the `YOSYS_RUN_ARGS` variable to pass arguments to Yosys. 
For instance, a script that lists all modules with the `keep_hierarchy` attribute set:

```bash
make DESIGN_CONFIG=designs/asap7/aes-block/config.mk synth run-yosys
```
