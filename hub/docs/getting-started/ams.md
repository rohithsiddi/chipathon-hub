# Track 2: Analog/Mixed-Signal (AMS) Flow

This track focuses on automating analog layout using open-source tools. For the Chipathon, contributions are typically made directly to the OpenFASOC / **GLayout** Repository.

## Core Installation
We require the following tools set up in a Python environment (≥ 3.10):
- Magic
- Netgen
- Yosys
- OpenROAD
- Open PDKs (GF180MCU and SKY130)
- NGSpice
- Klayout

> [!TIP]
> To test your installation, there is a script called `test_glayout.py` in the `openfasoc/generators/glayout`. Run this script to check if all the tools are installed correctly.

## GLayout Generators
A detailed introduction to GLayout and its codebase is necessary. GLayout uses Python-based layout generation (PCells).

### Important PCells to Study:
1. **Via Generator**: Demonstrates how to place a rectangular via by using specified metal layers. This is the simplest pcell and a must know.
2. **Current Mirror**: Covers the placement, movement and routing of a 2 transistor current mirror.
3. **Opamp**: Creates a two-stage Operational Amplifier + an nfet output stage. The opamp uses a differential to single-ended converter and a pmos load with miller compensation.
