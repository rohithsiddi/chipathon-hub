# Environment Issues

If your build fails before the flow even starts, or `make` complains it can't find rules, you likely have an environment issue.

### 1. `make: *** No rule to make target 'X'`
This usually means your `config.mk` path is wrong, or the target doesn't exist.
* Ensure you are running `make` from `OpenROAD-flow-scripts/flow`, not the root directory.

### 2. Apple Silicon Segfaults (Docker)
OpenROAD natively compiles for `linux/amd64`. Running standard docker containers on M-series Macs uses Rosetta 2 emulation.
* Yosys has known bugs under Rosetta. You *must* use `--platform linux/amd64` when starting your container.

### 3. Missing Dependencies on Bare Metal
If you aren't using Docker, ensure you ran:
```bash
./etc/DependencyInstaller.sh
./build_openroad.sh --local
```
Boost and Swig version mismatches are the leading cause of `cmake` failures.
