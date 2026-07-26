#!/usr/bin/env python3
"""
parse_uart.py

Universal UART Log Parser for ML-KEM Microcontroller Benchmarks.
Updates/appends parsed benchmark results into dataset/benchmark.csv without duplicating rows.
"""

import os
import re
import csv
import sys

CSV_PATH = os.path.join("dataset", "benchmark.csv")

MCU_SPECS = {
    "stm32f4":   {"mcu": "STM32F407VGT6", "core": "Cortex-M4",    "clock_mhz": 168, "flash_kb": 1024,  "ram_kb": 192},
    "stm32f0":   {"mcu": "STM32F072RBT6", "core": "Cortex-M0",    "clock_mhz": 48,  "flash_kb": 128,   "ram_kb": 16},
    "stm32h7":   {"mcu": "STM32H753ZIT6", "core": "Cortex-M7",    "clock_mhz": 480, "flash_kb": 2048,  "ram_kb": 1024},
    "nrf52840":  {"mcu": "nRF52840",      "core": "Cortex-M4",    "clock_mhz": 64,  "flash_kb": 1024,  "ram_kb": 256},
    "hifive1":   {"mcu": "HiFive1",       "core": "RISC-V FE310", "clock_mhz": 320, "flash_kb": 16384, "ram_kb": 16},
}

FIELDNAMES = [
    "mcu", "core", "clock_mhz", "flash_kb", "ram_kb",
    "variant", "keygen_cycles", "encap_cycles", "decap_cycles",
    "keygen_us", "encap_us", "decap_us",
    "keygen_stddev_us", "encap_stddev_us", "decap_stddev_us",
    "verification_status"
]

def parse_raw_log(target_name):
    target_name = target_name.lower()
    if target_name not in MCU_SPECS:
        print(f"Error: Unknown target '{target_name}'. Available: {list(MCU_SPECS.keys())}")
        return []

    spec = MCU_SPECS[target_name]
    raw_log = os.path.join("dataset", f"{target_name}_raw_output.txt")

    # Search for latest rotated log file if base file is empty
    log_file_to_read = raw_log
    if not os.path.exists(raw_log) or os.path.getsize(raw_log) == 0:
        for idx in range(1, 25):
            rot = f"{raw_log}.{idx}"
            if os.path.exists(rot) and os.path.getsize(rot) > 0:
                log_file_to_read = rot

    if not os.path.exists(log_file_to_read):
        print(f"Error: Log file {log_file_to_read} not found.")
        return []

    print(f"Parsing log file: {log_file_to_read} for target {spec['mcu']}...")
    with open(log_file_to_read, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    results = []
    # Pattern 1: Standard CSV row output
    pattern_std = re.compile(
        r"^(ML-KEM-(?:512|768|1024)),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),([01])$",
        re.MULTILINE
    )

    # Pattern 2: OOM CSV row output
    pattern_oom = re.compile(
        r"^(ML-KEM-(?:512|768|1024)),OOM,OOM,OOM,OOM,OOM,OOM,(\d+),(\d+),(\d+),OOM$",
        re.MULTILINE
    )

    matches_std = pattern_std.findall(content)
    for m in matches_std:
        variant, kg_cyc, enc_cyc, dec_cyc, kg_us, enc_us, dec_us, kg_std, enc_std, dec_std, ok = m
        results.append({
            "mcu": spec["mcu"],
            "core": spec["core"],
            "clock_mhz": str(spec["clock_mhz"]),
            "flash_kb": str(spec["flash_kb"]),
            "ram_kb": str(spec["ram_kb"]),
            "variant": variant,
            "keygen_cycles": str(kg_cyc),
            "encap_cycles": str(enc_cyc),
            "decap_cycles": str(dec_cyc),
            "keygen_us": str(kg_us),
            "encap_us": str(enc_us),
            "decap_us": str(dec_us),
            "keygen_stddev_us": str(kg_std),
            "encap_stddev_us": str(enc_std),
            "decap_stddev_us": str(dec_std),
            "verification_status": "PASS" if ok == "1" else "FAIL"
        })

    matches_oom = pattern_oom.findall(content)
    for m in matches_oom:
        variant, kg_std, enc_std, dec_std = m
        results.append({
            "mcu": spec["mcu"],
            "core": spec["core"],
            "clock_mhz": str(spec["clock_mhz"]),
            "flash_kb": str(spec["flash_kb"]),
            "ram_kb": str(spec["ram_kb"]),
            "variant": variant,
            "keygen_cycles": "OOM",
            "encap_cycles": "OOM",
            "decap_cycles": "OOM",
            "keygen_us": "OOM",
            "encap_us": "OOM",
            "decap_us": "OOM",
            "keygen_stddev_us": str(kg_std),
            "encap_stddev_us": str(enc_std),
            "decap_stddev_us": str(dec_std),
            "verification_status": "OOM"
        })

    return results

def update_csv_without_duplicates(new_records):
    if not new_records:
        return

    existing_rows = []
    if os.path.exists(CSV_PATH) and os.path.getsize(CSV_PATH) > 0:
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Keep valid data rows
                if row.get("mcu") and row.get("variant"):
                    existing_rows.append(row)

    # Build a lookup key (mcu, variant) to avoid duplicates
    new_keys = {(r["mcu"], r["variant"]): r for r in new_records}

    # Filter out old rows that are being updated by new_records
    filtered_rows = [r for r in existing_rows if (r.get("mcu"), r.get("variant")) not in new_keys]

    # Combine existing unique rows with updated new records
    final_rows = filtered_rows + new_records

    # Write back clean CSV
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for r in final_rows:
            writer.writerow(r)

    print(f"Updated {CSV_PATH} cleanly ({len(new_records)} records added/updated, total unique rows: {len(final_rows)})")

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/parse_uart.py <target_name>")
        print("Targets: stm32f4, stm32f0, stm32h7, nrf52840, hifive1")
        sys.exit(1)

    target = sys.argv[1]
    records = parse_raw_log(target)
    if records:
        update_csv_without_duplicates(records)
        print("Done!")
    else:
        print("No records found in raw log.")

if __name__ == "__main__":
    main()
