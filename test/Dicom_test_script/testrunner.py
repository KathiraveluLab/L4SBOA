#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import argparse
import json
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

# Configuration
SERVER_IP = "192.168.50.10"
PORT = "1104"
AET = "TEST_CLIENT"
AEC = "PACS_SERVER"

DICOM_DIR = os.path.expanduser("~/dicom_test")
LOG_DIR = os.path.expanduser("~/l4s_logs")

# Make sure log dir exists
os.makedirs(LOG_DIR, exist_ok=True)


def run_command(command, background=False):
    """Executes a shell command and returns output."""
    print(f"Executing: {command}")
    if background:
        return subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result


def test_connectivity():
    """Test basic connectivity to the server port."""
    print("Testing connection to Server...")
    try:
        with socket.create_connection((SERVER_IP, int(PORT)), timeout=3):
            print("Connection OK")
            return True
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        print(f"Connection Failed: {e}")
        return False


def get_network_stats():
    """Returns current TCP/ECN stats via 'ss' command"""
    res = run_command(f"ss -tin dst {SERVER_IP}")
    return res.stdout


def run_dicom_transfer(size_dir="medium"):
    """Runs storescu for DICOM transfers."""
    dataset_path = os.path.join(DICOM_DIR, size_dir)
    if not os.path.exists(dataset_path):
        print(f"Warning: Dataset path {dataset_path} does not exist. Skipping.")
        return None

    dicom_files = [os.path.join(dataset_path, f) for f in os.listdir(dataset_path) if f.endswith(".dcm")]
    if not dicom_files:
        print(f"Warning: No .dcm files found in {dataset_path}.")
        return None

    print(f"Starting {size_dir} DICOM transfer ({len(dicom_files)} files)...")

    start_time = time.time()

    # Capture before stats
    net_before = get_network_stats()

    cmd = f"find {shlex.quote(dataset_path)} -name '*.dcm' -print0 | xargs -0 -n 10 storescu -v -aet {AET} -aec {AEC} --max-pdu 65536 {SERVER_IP} {PORT}"

    result = run_command(cmd)

    end_time = time.time()
    elapsed = end_time - start_time

    # Capture after stats
    net_after = get_network_stats()

    print(f"Transfer took {elapsed:.2f} seconds.")

    # Calculate metrics
    # Calculate metrics from actual file sizes
    total_size_mib = sum(os.path.getsize(f) for f in dicom_files) / (1024 * 1024)  # Size in Mebibytes
    throughput_MiBps = (total_size_mib / elapsed) if elapsed > 0 else 0
    throughput_mbps = (total_size_bytes * 8) / elapsed / 1_000_000 if elapsed > 0 else 0

    return {
        "size_category": size_dir,
        "files_transferred": len(dicom_files),
        "transfer_time": elapsed,
        "throughput_mbps": throughput_mbps,
        "success": result.returncode == 0,
        "net_before": net_before,
        "net_after": net_after
    }


def run_iperf_test(duration=30):
    """Runs a bandwidth and latency test using iperf3."""
    print(f"Running iperf3 test to {SERVER_IP} for {duration} seconds...")
    cmd = f"iperf3 -c {SERVER_IP} -t {duration} -J"
    result = run_command(cmd)

    if result.returncode != 0:
        print("iperf3 test failed.")
        return None

    try:
        data = json.loads(result.stdout)
        end_data = data.get("end", {})
        sum_sent = end_data.get("sum_sent", {})

        throughput_bps = sum_sent.get("bits_per_second", 0)
        retransmits = sum_sent.get("retransmits", 0)

        return {
            "duration": duration,
            "throughput_mbps": throughput_bps / 1_000_000,
            "retransmits": retransmits
        }
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Failed to parse iperf3 JSON: {e}")
        return None


def run_flent_test(test_name="rrul", duration=60):
    """Runs a flent test (Realtime Response Under Load)."""
    print(f"Running flent {test_name} test for {duration}s...")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = os.path.join(LOG_DIR, f"flent_{test_name}_{timestamp}.flent.gz")
    cmd = f"flent {shlex.quote(test_name)} -p all_scaled -l {duration} -H {SERVER_IP} -o {shlex.quote(out_file)} --extended-metadata"
    cmd = f"flent {test_name} -p all_scaled -l {duration} -H {SERVER_IP} -o {out_file} --extended-metadata"
    result = run_command(cmd)

    if result.returncode == 0:
        print(f"Flent test completed. Results saved to {out_file}")
        return out_file
    else:
        print(f"Flent test failed: {result.stderr}")
        return None


def plot_results(results):
    """Uses matplotlib to visualize the transfer times and throughput."""
    if not results:
        return

    df = pd.DataFrame(results)

    # Plot 1: Transfer Times
    plt.figure(figsize=(10, 5))
    plt.bar(df['size_category'], df['transfer_time'])
    plt.title('DICOM Transfer Time by Dataset Size')
    plt.xlabel('Dataset Size Category')
    plt.ylabel('Time (Seconds)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    plot1_path = os.path.join(LOG_DIR, "transfer_times.png")
    plt.savefig(plot1_path)
    print(f"Saved plot: {plot1_path}")

    # Plot 2: Throughput
    plt.figure(figsize=(10, 5))
    plt.plot(df['size_category'], df['throughput_mbps'], marker='o', linestyle='-', color='red')
    plt.title('Throughput by Dataset Size')
    plt.xlabel('Dataset Size Category')
    plt.ylabel('Throughput (Mbps)')
    plt.grid(True)

    plot2_path = os.path.join(LOG_DIR, "throughput.png")
    plt.savefig(plot2_path)
    print(f"Saved plot: {plot2_path}")


def main():
    parser = argparse.ArgumentParser(description="L4SBOA Test Runner for DICOM, iperf, and Flent.")
    parser.add_argument("--skip-conn", action="store_true", help="Skip connection test.")
    parser.add_argument("--skip-dicom", action="store_true", help="Skip DICOM transfers.")
    parser.add_argument("--skip-iperf", action="store_true", help="Skip iperf3 tests.")
    parser.add_argument("--run-flent", action="store_true", help="Run Flent RRUL test.")

    args = parser.parse_args()

    print("=== Starting L4SBOA Test Runner ===")

    if not args.skip_conn:
        if not test_connectivity():
            sys.exit(1)

    all_dicom_results = []

    if not args.skip_dicom:
        # Create dummy directories if they don't exist
        for size in ["small", "medium", "large"]:
            path = os.path.join(DICOM_DIR, size)
            os.makedirs(path, exist_ok=True)
            # Create a dummy file just to allow the script to pass if empty
            if not os.listdir(path):
                run_command(f"touch {os.path.join(path, 'dummy.dcm')}")

        for size in ["small", "medium", "large"]:
            res = run_dicom_transfer(size)
            if res:
                all_dicom_results.append(res)

        # Generate Visualizations
        if all_dicom_results:
            plot_results(all_dicom_results)

    if not args.skip_iperf:
        iperf_res = run_iperf_test(duration=15)
        print("Iperf3 Results:", iperf_res)

    if args.run_flent:
        run_flent_test()

    print("=== Test Runner Complete ===")

if __name__ == "__main__":
    main()
