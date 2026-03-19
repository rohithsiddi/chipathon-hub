# Environment Setup

There are multiple ways to install and develop OpenROAD and ORFS. However, the best option depends on your use case, experience level, and personal preference.

## Recommendation for new users: Docker
If you are new to OpenROAD-flow-scripts, **Docker** can be a reliable way to get started since it avoids most dependency and environment issues. 
Docker image includes ORFS binaries, applications as well as all required dependencies. All of the flow tools are encapsulated inside the container image.

1. Ensure Docker is installed on your OS.
2. To manage docker as non-root user and verify that you can run docker commands without `sudo` must complete post-installation steps.
3. Build or pull ORFS with Docker.
- For Docker run `docker pull openroad/orfs:latest` to update the image.

## Alternative: Bazel-based Flow
`bazel-orfs` provides a seamless, reproducible way to manage dependencies and adapt the flow without requiring manual installations (no Docker images, sudo bash scripts, etc.).
By leveraging Bazel's robust build system, all dependencies are automatically resolved, versioned, and built in a consistent environment.

## Pre-built Binaries
You can download, set up and run ORFS easily with pre-built binaries, including OpenROAD, Yosys and Klayout. 
> [!WARNING]
> Only the latest version of OpenROAD is guaranteed to work with the latest version of ORFS. Versions provided by third-party vendors are not guaranteed to work.

## Building from your own git repository
ORFS supports hosting projects in your own git repository without the need to fork ORFS.
To build from your own git repository:

```bash
cd /home/me/myproject
make --file=~/OpenROAD-flow-scripts/flow/Makefile DESIGN_CONFIG=somefolder/config.mk ...
```
