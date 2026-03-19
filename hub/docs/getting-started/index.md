---
title: Getting Started
description: Start your Chipathon journey — environment setup, tool versions, and track overview
---

# Getting Started

Welcome to the Chipathon! This section walks you through everything needed before you write a single line of RTL.

## What You Need

| Requirement | Recommended Version | Notes |
|-------------|--------------------|-|
| Docker | ≥ 24.0 | Required for the ORFS flow container |
| GNU Make | ≥ 4.3 | Orchestrates the flow stages |
| Python | ≥ 3.10 | For flow scripts and utilities |
| Git | ≥ 2.40 | For repo management |
| RAM | ≥ 16 GB | 32 GB recommended for complex designs |
| Disk | ≥ 50 GB free | Intermediate files can be large |

---

## Environment Setup

### Option A — Docker (Recommended)

The fastest, most reproducible path. Everything is pre-installed inside the ORFS Docker image.

```bash
# Pull the OpenROAD flow scripts container
docker pull openroad/flow-ubuntu22.04-builder:latest

# Clone ORFS
git clone https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts.git
cd OpenROAD-flow-scripts

# Start the container (mounts your local ORFS dir)
docker run -it \
  -v $(pwd):/OpenROAD-flow-scripts \
  -w /OpenROAD-flow-scripts \
  openroad/flow-ubuntu22.04-builder:latest bash
```

!!! warning "Apple Silicon (M1/M2/M3)"
    Add `--platform linux/amd64` to the `docker run` command. Performance may be slower due to emulation.

### Option B — Native Install (Advanced)

```bash
# Clone and build OpenROAD from source
git clone --recursive https://github.com/The-OpenROAD-Project/OpenROAD.git
cd OpenROAD
./etc/DependencyInstaller.sh   # installs system deps (Ubuntu/Debian)
mkdir build && cd build
cmake ..
make -j$(nproc)
```

---

## Your First Flow Run

Once inside the Docker container (or native install), run the built-in nangate45 demo:

```bash
cd /OpenROAD-flow-scripts
make DESIGN_CONFIG=./flow/designs/nangate45/gcd/config.mk
```

Expected outputs in `flow/results/nangate45/gcd/`:

| File | What it is |
|------|-----------|
| `1_1_yosys.v` | Post-synthesis netlist |
| `3_5_route.def` | Post-routing DEF |
| `6_final.gds` | Final GDSII |
| `reports/` | Timing, power, DRC reports |

!!! success "Success Criteria"
    If you see `[FLOW] Elapsed time: ...` without errors, your environment is working.

---

## Track Overview

The Chipathon typically runs multiple tracks with different target PDKs and design constraints.

| Track | PDK | Typical Constraints |
|-------|-----|---------------------|
| Digital | Nangate45 / SKY130 | Timing closure, area |
| Mixed-Signal | SKY130 | Analog blocks + digital integration |
| Advanced | ASAP7 | Advanced node EDA challenges |

!!! info "Check Your Track Config"
    Your track's `config.mk` defines your PDK, clock period, and die area. Always start from the provided template — do **not** start from scratch.
