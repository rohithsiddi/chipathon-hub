---
title: Environment Setup
description: Install Docker, set up your development environment for OpenROAD flow
---

# Environment Setup

## Docker Install (Recommended)

```bash
# Pull the ORFS container
docker pull openroad/flow-ubuntu22.04-builder:latest

# Clone ORFS
git clone https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts.git
cd OpenROAD-flow-scripts

# Run container
docker run -it \
  -v $(pwd):/OpenROAD-flow-scripts \
  -w /OpenROAD-flow-scripts \
  openroad/flow-ubuntu22.04-builder:latest bash
```

## Docker

!!! warning "Apple Silicon"
    Add `--platform linux/amd64` to the `docker run` command on M1/M2/M3 Macs.

## Native Install

```bash
git clone --recursive https://github.com/The-OpenROAD-Project/OpenROAD.git
cd OpenROAD
./etc/DependencyInstaller.sh
mkdir build && cd build
cmake ..
make -j$(nproc)
```

## Verifying Your Install

```bash
openroad -version
# Expected: OpenROAD X.Y.Z ...
```
