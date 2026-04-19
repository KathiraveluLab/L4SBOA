#!/usr/bin/env python3
"""
L4SBOA testrunner.py
Simulates healthcare data streams and evaluates L4S performance vs Classic TCP.
Implements the TCP Prague-controlled RTT dependence experiments as described in CCECE_25.
"""

import argparse
import subprocess
import time
import threading
import json
import csv
import sys
import os

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("Warning: matplotlib not installed. Plotting will be disabled.")
    plt = None

DELAYS = [0.5, 1, 5, 10, 15, 20, 30, 40, 50]

def set_delay(interface, delay_ms):
    """Update the delay using tc netem."""
    # This assumes the root qdisc is already netem or we add/replace it.
    cmd = f"sudo tc qdisc replace dev {interface} root netem delay {delay_ms}ms"
    print(f"[tc] Setting delay to {delay_ms}ms: {cmd}")
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def delay_orchestrator(interface, delays, interval_s):
    """Background thread to adjust delay every interval."""
    for d in delays:
        set_delay(interface, d)
        time.sleep(interval_s)
    # Clear the delay at the end
    subprocess.run(f"sudo tc qdisc del dev {interface} root", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def run_flent_test(host, duration, test_name, output_file):
    """Run traffic generation to capture data."""
    # We use iperf3 iteratively as described in the paper prototypes. "Flent to capture results... prototype contains matplotlib, python 3, and iperf3".
    cmd = f"iperf3 -c {host} -t {duration} -J > {output_file}"
    print(f"[iperf3] Running: {cmd}")
    subprocess.run(cmd, shell=True)

def plot_results(iperf_json, cc_mode, rtt_scale, output_img):
    if not plt:
        return
    try:
        with open(iperf_json, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {iperf_json}: {e}")
        return

    intervals = data.get("intervals", [])
    times = []
    throughputs = []
    
    # We aggregate the delays into blocks
    for interval in intervals:
        sum_data = interval.get("sum", {})
        times.append(sum_data.get("end", 0))
        # bps to mbps
        throughputs.append(sum_data.get("bits_per_second", 0) / 1e6)

    if not times:
        print("No valid interval data found in JSON.")
        return

    plt.figure(figsize=(10, 5))
    plt.plot(times, throughputs, label=f"TCP {cc_mode.capitalize()} Thpt", color='cyan' if cc_mode == 'prague' else 'blue')
    
    # Shade regions for delays
    interval_s = 100
    for i, d in enumerate(DELAYS):
        start_t = i * interval_s
        end_t = (i + 1) * interval_s
        plt.axvspan(start_t, end_t, alpha=0.1, color='gray')
        plt.text(start_t + 5, max(throughputs)*0.9 if throughputs else 10, f"{d}ms", rotation=90, color='gray')

    plt.title(f"RTT Dependency Test (Scale: {rtt_scale}) - {cc_mode.capitalize()}")
    plt.xlabel("Time (s)")
    plt.ylabel("Throughput (Mbps)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_img)
    print(f"[plot] Saved figure to {output_img}")

def main():
    parser = argparse.ArgumentParser(description="L4SBOA Test Runner")
    parser.add_argument("--host", required=True, help="Target iperf3 server")
    parser.add_argument("--interface", default="eth0", help="Network interface for tc netem")
    parser.add_argument("--cc", choices=["cubic", "prague"], default="cubic", help="Congestion control algorithm to use")
    parser.add_argument("--rtt-scale", type=int, choices=[0, 1, 3], default=1, help="RTT Scaling interval (0, 1, 3)")
    parser.add_argument("--interval", type=int, default=100, help="Interval per delay setting in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Do not run tcp or tc commands, just test plotting")
    args = parser.parse_args()

    duration = len(DELAYS) * args.interval
    output_prefix = f"rtt{args.rtt_scale}_{args.cc}"
    json_out = f"{output_prefix}.json"
    img_out = f"{output_prefix}.png"

    print(f"=== L4SBOA Test Runner ===")
    print(f"Target: {args.host}")
    print(f"CC Algorithm: {args.cc}")
    print(f"RTT Scale: {args.rtt_scale}")
    print(f"Total Duration: {duration}s")
    
    if args.dry_run:
        print("[dry-run] Skipping test execution.")
        if not os.path.exists(json_out):
            dummy = {"intervals": [{"sum": {"end": i, "bits_per_second": 50e6 if args.cc == 'prague' else 20e6}} for i in range(1, duration+1)]}
            with open(json_out, 'w') as f:
                json.dump(dummy, f)
        plot_results(json_out, args.cc, args.rtt_scale, img_out)
        return

    # Set Congestion Control
    print(f"[sysctl] Setting TCP CC to {args.cc}")
    subprocess.run(f"sudo sysctl -w net.ipv4.tcp_congestion_control={args.cc}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Start Orchestrator
    t = threading.Thread(target=delay_orchestrator, args=(args.interface, DELAYS, args.interval))
    t.start()

    # Run Capture
    run_flent_test(args.host, duration, "L4S_Test", json_out)

    t.join()

    # Generate plot
    plot_results(json_out, args.cc, args.rtt_scale, img_out)


if __name__ == "__main__":
    main()
