# Understanding OpenROAD Flow Scripts (ORFS)

The OpenROAD ("Foundations and Realization of Open, Accessible Design") project aims to bring down the barriers of cost, expertise and unpredictability that currently block designers access to hardware implementation in advanced technologies. 

OpenROAD Flow is a full RTL-to-GDS flow built entirely on open-source tools. The project aims for automated, no-human-in-the-loop (NHIL) digital circuit design with 24-hour turnaround time.

## `variables.mk`
ORFS defines tcl scripts and variables that can be used to implement a flow. Variables in EDA flows is an idiomatic domain feature: placement density, list of .lib, .lef files, etc.
The variables are implemented using the `make` language, which ORFS makes no effort to hide. Beyond make, ORFS uses Python and bash to implement the variables.

ORFS avoids the inversion of control trap where the user wants to be in control of the flow and also ORFS wants to be in the flow. To ORFS all build systems are first class citizens. The job of ORFS is to define and support an interface such that the user can pick a flow implementation that balances simplicity and required features.

```bash
# Print any variable in .yaml syntax
make print-CORE_UTILIZATION print-PLACE_DENSITY > foo.yaml
```

## `flow.sh` and `synth.sh`
Utility scripts that can be used in combination with `variables.mk` to invoke synthesis and flow steps without going through the ORFS Makefile.

`make run-yosys` sets up all the ORFS environment variables and launches Yosys. Useful to run a Yosys script or interactive mode on the synthesis result to extract information or debug synthesis results.
