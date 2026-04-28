# L4SBOA: TeleHealth Over L4S

**L4SBOA** (pronounced [Lisboa](https://pt.wikipedia.org/wiki/Lisboa)) is an L4S-based experimental network orchestration framework designed for optimizing Telehealth applications. It systematically evaluates the performance of L4S (Low Latency, Low Loss, and Scalable Throughput) against classic Internet congestion control protocols (like TCP Cubic) for delay-critical use-cases such as:

- **DICOM Imaging**: High-volume, loss-intolerant data streams for diagnostics.
- **Televisits / Video Streams**: Real-time communication requiring steady flows and minimal latency variation.
- **Wearable Telemonitoring**: Low-volume, ultra-low latency critical data.

---

## Getting Started

To fully utilize the L4SBOA framework, your test network requires pairs of nodes configured with L4S-enabled networking stacks.

### 1. Environment Setup

Both the client (sender) and server (receiver) nodes must be patched to support the TCP Prague congestion control algorithm and the DualQ Coupled Active Queue Management (AQM).

For step-by-step kernel installation and verification instructions, please review the setup guide:
**[L4S Kernel Patch Setup Guide](L4SkernelPatchSetUp.md)**

---

## Running the Framework

The L4SBOA framework offers two primary automated evaluation modules depending on your research target.

### Module A: RTT Dependency Simulator (Benchmark Suite)

To orchestrate exact replicas of the preliminary research assessments (as detailed in the CCECE_25 manuscript) and automatically generate RTT dependency throughput charts, use the provided Python Test Runner.

**1. Install Dependencies**

It is recommended to use a virtual environment to avoid conflicts with your system's Python packages:

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the required packages
pip install -r requirements.txt
```

**2. Run the Simulator**
The test runner integrates with `tc qdisc` and `iperf3` to seamlessly simulate varying synthetic network delays (from 0.5ms to 50ms gaps) over a continuous `900s` scalable interval context.

> **Note**: Since the script requires `sudo` for network configuration, you should run it using the virtual environment's Python interpreter:

```bash
# Run assessment against standard TCP Cubic
sudo .venv/bin/python testrunner.py --host <target_iperf_server_ip> --cc cubic --rtt-scale 1

# Run assessment against L4S TCP Prague
sudo .venv/bin/python testrunner.py --host <target_iperf_server_ip> --cc prague --rtt-scale 1
```

**Visualization**: Upon completion, the script parses the metrics and uses `matplotlib` to render shaded dependency plots (e.g., `rtt1_prague.png`) demonstrating the scalable throughput capacities.
> *Note: Use the `--dry-run` flag to test the plotting logic instantly without an active `iperf3` connection.*

### Module B: DICOM Transfer Evaluation

This module evaluates application-layer performance by transferring medical DICOM datasets utilizing standard hospital PACS utilities (`storescp` / `storescu`).

**1. Prepare the Environment**
Set up the `storescp` receiver on the destination L4S node:
```bash
storescp -v -aet PACS_SERVER -od ~/dicom_received 1104
```

**2. Execute the Transfers**
Use the provided bash orchestration scripts to automate baseline and congested transfers across small, medium, and large clinical datasets:
```bash
./test/Dicom_test_script/test_script.sh
```

For exhaustive evaluation architectures and customization, please review the full DICOM documentation:
**[DICOM Transfer Testing Guide](DicomTransferTest.md)**

---

## Research Context & Objectives

The telehealth consultation evaluation was initiated as part of a **Google Summer Of Code 2024** project targeting improved healthcare network optimization for rural communities (e.g., in Alaska).



## Citation

If you use this work in your research, please cite the following publication:

* Daramola K, Murphy R, Kathiravelu P. **L4S Bandwidth Orchestration Architecture: A Case for Network Optimization for Healthcare.** In 2025 IEEE Canadian Conference on Electrical and Computer Engineering (CCECE) 2025 May 26 (pp. 1-5). IEEE.