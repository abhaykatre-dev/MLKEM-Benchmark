#!/usr/bin/env python3
"""
automate_renode_benchmarks.py — Automated Real Renode Simulation Runner

Runs REAL headless Renode simulations for target microcontrollers, captures raw UART logs,
parses the actual execution time output, and populates benchmark.csv with REAL simulation data.
"""

import os
import subprocess
import sys
import time
import re
import csv

RENODE_EXE = r"C:\Program Files\Renode\renode.exe"
RESC_DIR   = os.path.join("renode")
DATASET_DIR= os.path.join("dataset")
CSV_PATH   = os.path.join(DATASET_DIR, "benchmark.csv")

# MCU Simulation Configurations to execute via Renode
SIMULATION_TARGETS = [
    {
        "mcu": "STM32F407VGT6",
        "core": "Cortex-M4",
        "clock_mhz": 168,
        "flash_kb": 1024,
        "ram_kb": 192,
        "resc": os.path.join(RESC_DIR, "stm32f4", "stm32f4_bench.resc"),
        "raw_log": os.path.join(DATASET_DIR, "stm32f4_raw_output.txt"),
        "timeout": 45
    },
    {
        "mcu": "STM32F072RBT6",
        "core": "Cortex-M0",
        "clock_mhz": 48,
        "flash_kb": 128,
        "ram_kb": 16,
        "resc": os.path.join(RESC_DIR, "stm32f0", "stm32f0_bench.resc"),
        "raw_log": os.path.join(DATASET_DIR, "stm32f0_raw_output.txt"),
        "timeout": 45
    },
    {
        "mcu": "STM32H753ZIT6",
        "core": "Cortex-M7",
        "clock_mhz": 480,
        "flash_kb": 2048,
        "ram_kb": 1024,
        "resc": os.path.join(RESC_DIR, "stm32h7", "stm32h7_bench.resc"),
        "raw_log": os.path.join(DATASET_DIR, "stm32h7_raw_output.txt"),
        "timeout": 45
    },
    {
        "mcu": "nRF52840",
        "core": "Cortex-M4",
        "clock_mhz": 64,
        "flash_kb": 1024,
        "ram_kb": 256,
        "resc": os.path.join(RESC_DIR, "nrf52840", "nrf52840_bench.resc"),
        "raw_log": os.path.join(DATASET_DIR, "nrf52840_raw_output.txt"),
        "timeout": 45
    },
    {
        "mcu": "HiFive1",
        "core": "RISC-V FE310",
        "clock_mhz": 320,
        "flash_kb": 16384,
        "ram_kb": 16,
        "resc": os.path.join(RESC_DIR, "hifive1", "hifive1_bench.resc"),
        "raw_log": os.path.join(DATASET_DIR, "hifive1_raw_output.txt"),
        "timeout": 45
    }
]

def kill_existing_renode():
    if sys.platform == "win32":
        subprocess.run(["powershell", "-Command", "Stop-Process -Name 'renode' -Force -ErrorAction SilentlyContinue"], capture_output=True)
        time.sleep(1)

def run_renode_simulation(target):
    print(f"\n[RUNNING REAL RENODE SIMULATION] Target: {target['mcu']} ({target['core']} @ {target['clock_mhz']} MHz)...")
    kill_existing_renode()

    resc_path = os.path.abspath(target["resc"])
    raw_log_path = os.path.abspath(target["raw_log"])

    if not os.path.exists(resc_path):
        print(f"Error: Script {resc_path} not found.")
        return []

    # Command to run Renode headlessly
    cmd = [RENODE_EXE, "-e", f"s @{resc_path}"]
    
    print(f"  Command: {RENODE_EXE} -e \"s @{resc_path}\"")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print(f"  Waiting {target['timeout']} seconds for simulation to complete in Renode...")
    time.sleep(target["timeout"])

    kill_existing_renode()
    print(f"  Simulation finished for {target['mcu']}. Reading raw UART log...")

    # Find log file (handles Renode log file rotation like .1, .2, etc.)
    log_candidates = [raw_log_path]
    for ext in range(1, 20):
        c = f"{raw_log_path}.{ext}"
        if os.path.exists(c):
            log_candidates.append(c)

    best_log = None
    for c in reversed(log_candidates):
        if os.path.exists(c) and os.path.getsize(c) > 100:
            best_log = c
            break

    if not best_log:
        print(f"  Warning: No non-empty UART log found for {target['mcu']}.")
        return []

    print(f"  Found UART log: {best_log} ({os.path.getsize(best_log)} bytes)")
    return parse_uart_log(best_log, target)

def parse_uart_log(log_path, target):
    results = []
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Match CSV rows from raw UART output
    pattern = re.compile(
        r"^(ML-KEM-(?:512|768|1024)),(\w+),(\w+),(\w+),(\w+),(\w+),(\w+),(\d+),(\d+),(\d+),(\w+)$",
        re.MULTILINE
    )

    matches = pattern.findall(content)
    if not matches:
        # Fallback pattern for OOM lines
        pattern_oom = re.compile(r"^(ML-KEM-(?:512|768|1024)),OOM,OOM,OOM,OOM,OOM,OOM,(\d+),(\d+),(\d+),OOM$", re.MULTILINE)
        matches = pattern_oom.findall(content)

    for m in matches:
        variant, kg_cyc, enc_cyc, dec_cyc, kg_us, enc_us, dec_us, kg_std, enc_std, dec_std, ok = m
        results.append({
            "mcu": target["mcu"],
            "core": target["core"],
            "clock_mhz": target["clock_mhz"],
            "flash_kb": target["flash_kb"],
            "ram_kb": target["ram_kb"],
            "variant": variant,
            "keygen_cycles": kg_cyc,
            "encap_cycles": enc_cyc,
            "decap_cycles": dec_cyc,
            "keygen_us": kg_us,
            "encap_us": enc_us,
            "decap_us": dec_us,
            "keygen_stddev_us": kg_std,
            "encap_stddev_us": enc_std,
            "decap_stddev_us": dec_std,
            "verification_status": "PASS" if ok == "1" else ("OOM" if ok == "OOM" else "FAIL")
        })

    return results

def main():
    print("=========================================================================")
    print("  REAL RENODE SIMULATION AUTOMATION PIPELINE FOR ML-KEM BENCHMARKING    ")
    print("=========================================================================")

    all_records = []

    for target in SIMULATION_TARGETS:
        records = run_renode_simulation(target)
        if records:
            all_records.extend(records)
            print(f"  [SUCCESS] Captured {len(records)} real simulation records for {target['mcu']}.")
        else:
            print(f"  [FAILED] No records captured for {target['mcu']}.")

    if all_records:
        os.makedirs(DATASET_DIR, exist_ok=True)
        fieldnames = list(all_records[0].keys())
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in all_records:
                writer.writerow(r)
        print("\n=========================================================================")
        print(f"  SUCCESSFULLY SAVED {len(all_records)} REAL RENODE BENCHMARK ROWS TO:")
        print(f"  {os.path.abspath(CSV_PATH)}")
        print("=========================================================================")
    else:
        print("\nNo records captured from Renode simulations.")

if __name__ == "__main__":
    main()
