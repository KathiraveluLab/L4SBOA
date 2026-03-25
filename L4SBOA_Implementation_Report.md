# L4SBOA Repository Implementation Report

Based on the paper "L4SBOA," the proposed bandwidth orchestration mechanism involves using L4S (Low Latency, Low Loss, Scalable Throughput) configuration combined with ECN adjustments, TCP Prague, and DUALQ Coupled AQM. The paper explicitly lists the use of specific visualization and network testing tools like Flent, `iperf3`, `matplotlib`, and a `testrunner.py` script to simulate healthcare data streams (specifically telehealth, telemonitoring, and televisits).

Here is a breakdown of the repository's features in comparison to the claims made in the provided text from the L4SBOA paper:

## Features Present in the Repository:
1. **L4S Configuration and Operating System**: The repository thoroughly documents installing the L4S patches on the Linux kernel, configuring TCP congestion control to Prague, and using the `sysctl -w net.ipv4.tcp_congestion_control=prague` command (present in `L4SkernelPatchSetUp.md`).
2. **DUALQ Coupled AQM**: The deployment setup for the L4S queue structure is fully detailed in the repository via `tc qdisc replace dev eno1 root dualpi2`.
3. **iperf3**: Extensive usage instructions and bash scripts using `iperf3` to perform network benchmarking are provided for L4S performance testing.
4. **Healthcare Data Simulation**: The repository correctly includes testing and benchmarking methods for the healthcare use cases, specifically DICOM (Digital Imaging and Communications in Medicine) file transfers. The bash scripts `l4s_transfer.sh` and `test_script.sh` use `storescu` and `storescp` tools to test DICOM file transmissions over L4S nodes.
5. **Python 3**: Python 3 is present on the environment but is not extensively used for custom simulation scripts in the repository as described in the paper; instead, Bash scripts fulfill the simulation role.

## Features Missing from the Repository:
1. **Flent**: The paper states that Flent is used to capture results from tests on L4S. A comprehensive search throughout the repository (`grep -rnw '/app' -e 'flent' -i`) yielded no results. There are no Flent configuration files or scripts.
2. **matplotlib**: The paper states that `matplotlib` is used to visualize network performance. Searching for `matplotlib` across the codebase resulted in no mentions. Data visualization elements are completely absent from the current codebase.
3. **testrunner.py**: The paper explicitly references a `testrunner.py` code to perform the experiments. This file does not exist in the repository. Instead, there are bash scripts (`l4s_transfer.sh`, `test_script.sh`) inside `test/Dicom_test_script/` which currently run the experiments.
4. **VM Machine Instances**: The paper discusses developing L4SBOA as VM machine instances that can be installed easily across servers. There are no virtualization files (like Vagrantfiles, Dockerfiles, or VM images) that simplify this setup process in the current codebase, only documentation for bare-metal/manual VM kernel compilation (`L4SkernelPatchSetUp.md`).

## Conclusion:
The repository successfully implements the core networking features proposed by L4SBOA (L4S kernel patches, TCP Prague, DualQ Coupled AQM) and includes functional bash scripts for testing healthcare (DICOM) data streams over these nodes via `iperf3` and DICOM utilities.

However, the analytical layer (Flent, matplotlib) and specific scripts (`testrunner.py`) described in the paper are missing from the current repository. The experiments seem to have been shifted from Python (`testrunner.py`) to Bash (`test_script.sh`).
