---
title: FAQ
description: Canonical answers to the most common Chipathon and OpenROAD flow questions
tags:
  - OpenROAD
  - Setup
  - Timing
  - DRC
  - Routing
---

# Frequently Asked Questions

These are real questions asked during past Chipathons, with answers from mentors and maintainers.

---

## Environment & Setup

??? question "Docker fails to start the container — 'permission denied'"
    **Answer:** Add your user to the `docker` group and restart your session:
    ```bash
    sudo usermod -aG docker $USER
    newgrp docker
    ```
    If on macOS, ensure Docker Desktop is running and has sufficient resources (≥16 GB RAM allocation).

??? question "The flow works locally but fails in CI — why?"
    **Answer:** CI usually has less RAM. Add `NPROC=2` or set `-j2` in your CI Makefile target. Also check that your Docker image tag is pinned (don't use `latest` in CI — use a specific version tag like `v3.0`).

??? question "What OpenROAD version should I use for the Chipathon?"
    **Answer:** Use the version specified in your track's `config.mk` or the one pinned in the Chipathon starter repo. Mismatched versions are a top cause of unexpected failures. Run `openroad -version` to verify.

---

## Flow Configuration

??? question "How do I change the clock period?"
    **Answer:** In your `config.mk`:
    ```makefile
    export CLOCK_PERIOD = 2.0  # in nanoseconds
    ```
    Start with a relaxed period (e.g. 5 ns for simple designs on Nangate45) and tighten incrementally.

??? question "I only want to re-run one stage (e.g., routing) — how?"
    **Answer:** Use stage-specific make targets:
    ```bash
    make clean_drt            # clean detailed routing artifacts
    make DESIGN_CONFIG=... 5_route   # re-run from detailed routing
    ```
    Available targets: `1_synth`, `2_floorplan`, `3_place`, `4_cts`, `5_route`, `6_finish`.

??? question "What does CORE_UTILIZATION control?"
    **Answer:** It's the percentage of the core area filled with standard cells (not including routing channels). Values above 70% risk routing congestion. Start at 40–50% and increase once your design closes.

---

## Timing

??? question "I have setup violations (negative WNS). What should I do first?"
    **Answer:** Follow this checklist in order:
    1. Check if the clock period is realistic for your design complexity
    2. Look at the worst path in `6_final_report.rpt` — is it a real path or a false path?
    3. Enable `GPL_ROUTABILITY_DRIVEN = 1` in config.mk
    4. Try `export DPO_MAX_DISPLACEMENT = 5 5` for post-route optimization
    5. If all else fails, relax `CLOCK_PERIOD` by 0.2 ns increments

??? question "What is WNS vs TNS?"
    **Answer:**
    - **WNS (Worst Negative Slack):** The single worst timing violation. If negative, your worst path fails timing.
    - **TNS (Total Negative Slack):** Sum of all violations. A large TNS with small WNS means many marginal paths.
    Both must be ≥ 0 for timing closure.

---

## DRC & Routing

??? question "I have DRC violations I can't clear. What are my options?"
    **Answer:** Common approaches:
    1. Enable antenna repair: `export ANTENNA_REPAIR = 1`
    2. Lower routing density: `export ROUTING_TARGET_DENSITY = 0.60`
    3. Increase die area (reduce `CORE_UTILIZATION`)
    4. Check if the violated rule is a PDK-specific rule you need to waive with your mentor

??? question "The router hangs / takes forever. How do I debug?"
    **Answer:**
    - Set `export GLOBAL_ROUTE_ARGS = -congestion_iterations 30` to limit GRT iterations
    - Monitor progress: `tail -f flow/logs/<pdk>/<design>/5_1_grt.log`
    - If memory OOM: reduce `-j` parallelism and check `CORE_UTILIZATION`

---

## Submission

??? question "What files do I need to submit?"
    **Answer:** At minimum:
    - `6_final.gds` — final GDSII
    - `6_final.def` — final DEF
    - `reports/6_final_report.rpt` — timing report
    - `reports/6_drc.rpt` — DRC report showing 0 violations
    - `reports/metrics.json` — QoR summary

    See the [Artifact Map](artifact-map.md) for the full checklist.

??? question "My GDS has 0 DRC but my timing has negative slack. Will I be disqualified?"
    **Answer:** Depends on the track rules. Most tracks require both: DRC-clean AND timing closure. Check your specific track's acceptance criteria. A design with small violations may still be evaluated for partial credit — ask your mentor.

---

!!! tip "Didn't find your question?"
    Try the [Ask Chipathon chatbot](chatbot.md) or search the [OpenROAD GitHub Issues](https://github.com/The-OpenROAD-Project/OpenROAD/issues).
