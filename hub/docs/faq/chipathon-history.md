# "Seen During Chipathon" Databank

This page tracks canonical solutions developed by mentors on Discord or GitHub issues to solve novel, Hackathon-specific bugs.

## How do I get better search results?
Search functionality is built directly into this Knowledge Hub. Use specific keywords from your OpenROAD logs (like `RSZ-0062` or `GRT-0118`) instead of generally searching "How to fix congestion."

## How do I update OpenROAD Flow Scripts?
If you are using Docker, simply run:
```bash
docker pull openroad/orfs:latest
```
For local installs, checking out `master` and running `./build_openroad.sh --local` is recommended to fetch submodule updates.

## I get a `fatal error` when making a new layout in GLayout (AMS Track)
If you are generating a via or current mirror and it fails to display in KLayout or Magic, ensure your conda environment has python ≥ 3.10 and you ran `test_glayout.py` from the `openfasoc/generators/glayout` directory prior to designing your PCells.
