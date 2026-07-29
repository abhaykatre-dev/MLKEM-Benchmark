#!/usr/bin/env python3
"""
rebuild_dataset_from_logs.py — Research-Grade Dataset Reconstruction Tool

Reconstructs dataset/benchmark_renode_measurements.csv from ALL existing raw UART
log files in dataset/raw_logs/, matched against firmware/builds/build_manifest.json.

This script is the authoritative dataset rebuilder. It handles both log naming
conventions produced by the project:
  - {experiment_id}.txt          (primary convention used by STM32H7/F0 logs)
  - {experiment_id}_run001.txt   (run-indexed convention used by STM32F4 logs)

Each CSV row is cryptographically anchored to its source log file (SHA-256) and
its compiled ELF binary (SHA-256 from the build manifest). The resulting dataset
is suitable for inclusion in peer-reviewed research.

Usage:
    python scripts/rebuild_dataset_from_logs.py [--dry-run]

Author: ML-KEM Benchmark Project
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "firmware" / "builds" / "build_manifest.json"
LOGS_DIR = ROOT / "dataset" / "raw_logs"
DATASET_PATH = ROOT / "dataset" / "benchmark_renode_measurements.csv"
REPORT_PATH = ROOT / "dataset" / "validation_report.json"

# ---------------------------------------------------------------------------
# CSV column schema — fixed ordering for reproducibility
# ---------------------------------------------------------------------------
FIELDS = [
    "experiment_id",
    "run_id",
    "measurement_type",
    "mcu",
    "board_model",
    "core",
    "configured_clock_mhz",
    "variant",
    "opt_level",
    "iteration_count",
    "keygen_timer_ticks",
    "keygen_us",
    "encap_timer_ticks",
    "encap_us",
    "decap_timer_ticks",
    "decap_us",
    "keygen_stddev_us",
    "encap_stddev_us",
    "decap_stddev_us",
    "hardware_cycle_count_or_na",
    "estimated_cycles_or_na",
    "text_bytes",
    "rodata_bytes",
    "data_bytes",
    "bss_bytes",
    "flash_bytes",
    "static_ram_bytes",
    "peak_stack_bytes_or_na",
    "peak_total_ram_bytes",
    "verification_status",
    "run_status",
    "compiler_version",
    "renode_version",
    "source_revision",
    "elf_sha256",
    "raw_log_file",
    "raw_log_sha256",
    "timestamp_utc",
]

# Regex matching the single CSV data line emitted by the firmware's benchmark harness:
# variant,keygen_cycles,encap_cycles,decap_cycles,keygen_us,encap_us,decap_us,
#         keygen_stddev,encap_stddev,decap_stddev,decap_ok,peak_stack
_DATA_RE = re.compile(
    r"^(ML-KEM-(?:512|768|1024)),"   # variant
    r"(\d+),"                         # keygen_cycles
    r"(\d+),"                         # encap_cycles
    r"(\d+),"                         # decap_cycles
    r"(\d+),"                         # keygen_us
    r"(\d+),"                         # encap_us
    r"(\d+),"                         # decap_us
    r"(\d+),"                         # keygen_stddev
    r"(\d+),"                         # encap_stddev
    r"(\d+),"                         # decap_stddev
    r"([01]),"                        # decap_ok
    r"(\d+)$",                        # peak_stack_bytes
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    """Return the hex SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_uart_log(log_path: Path) -> dict | None:
    """
    Parse a Renode UART log file produced by the ML-KEM benchmark firmware.

    Returns a dict of parsed fields, or None if the log is incomplete / malformed.
    """
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    if "BENCHMARK SUITE COMPLETE!" not in text:
        return None

    match = _DATA_RE.search(text)
    if match is None:
        return None

    (
        variant,
        keygen_cycles, encap_cycles, decap_cycles,
        keygen_us, encap_us, decap_us,
        keygen_stddev, encap_stddev, decap_stddev,
        decap_ok,
        peak_stack,
    ) = match.groups()

    return {
        "variant": variant,
        "keygen_cycles": int(keygen_cycles),
        "encap_cycles": int(encap_cycles),
        "decap_cycles": int(decap_cycles),
        "keygen_us": int(keygen_us),
        "encap_us": int(encap_us),
        "decap_us": int(decap_us),
        "keygen_stddev": int(keygen_stddev),
        "encap_stddev": int(encap_stddev),
        "decap_stddev": int(decap_stddev),
        "decap_ok": int(decap_ok),
        "peak_stack_bytes": int(peak_stack),
    }


def find_all_logs_for_experiment(exp_id: str) -> list[tuple[Path, int]]:
    """
    Find ALL available raw log files for a given experiment ID.

    Returns a list of (path, run_id) tuples so every independent Renode
    simulation run becomes its own row in the dataset.

    Priority ordering within the same run_id:
      {exp_id}_run001.txt  (run-indexed form, preferred — from run_renode_simulations.py)
      {exp_id}.txt         (unindexed form — from earlier/legacy simulation runs)
    """
    found: list[tuple[Path, int]] = []

    # First: run-indexed logs ({exp_id}_runNNN.txt)
    for candidate in sorted(LOGS_DIR.glob(f"{exp_id}_run*.txt")):
        m = re.search(r"_run(\d+)\.txt$", candidate.name)
        if m and candidate.stat().st_size > 0:
            found.append((candidate, int(m.group(1))))

    # Second: unindexed log ({exp_id}.txt) — treated as an additional independent run
    unindexed = LOGS_DIR / f"{exp_id}.txt"
    if unindexed.exists() and unindexed.stat().st_size > 0:
        # Assign run_id = max_existing + 1 to avoid collisions
        existing_ids = {rid for _, rid in found}
        next_id = max(existing_ids) + 1 if existing_ids else 1
        found.append((unindexed, next_id))

    return found


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Rebuild benchmark_renode_measurements.csv from raw UART logs.",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate without writing output files.",
    )
    args = ap.parse_args()

    # ------------------------------------------------------------------
    # Load build manifest
    # ------------------------------------------------------------------
    if not MANIFEST_PATH.exists():
        raise SystemExit(f"[ERROR] Build manifest not found: {MANIFEST_PATH}")

    manifest_data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    all_builds: dict[str, dict] = manifest_data["builds"]
    renode_version = "Renode v1.16.1.19220"  # Version used for all Renode runs
    source_revision = "unversioned-worktree"

    timestamp = datetime.now(timezone.utc).isoformat()

    print("=" * 72)
    print("  ML-KEM BENCHMARK DATASET RECONSTRUCTION")
    print("  Source: firmware/builds/build_manifest.json")
    print(f"  Logs:   dataset/raw_logs/ ({sum(1 for _ in LOGS_DIR.glob('*.txt'))} .txt files present)")
    print("=" * 72)

    rows: list[dict] = []
    skipped_no_log: list[str] = []
    skipped_parse_fail: list[str] = []
    skipped_variant_mismatch: list[str] = []
    skipped_build_failed: list[str] = []

    for exp_id, build_info in sorted(all_builds.items()):
        # Only include experiments where the build succeeded
        if build_info.get("build_status") != "SUCCESS":
            skipped_build_failed.append(exp_id)
            continue

        all_logs = find_all_logs_for_experiment(exp_id)
        if not all_logs:
            skipped_no_log.append(exp_id)
            continue

        for log_path, run_id in all_logs:
            parsed = parse_uart_log(log_path)
            if parsed is None:
                skipped_parse_fail.append(f"{exp_id} run{run_id}")
                print(f"  [SKIP] {exp_id} run{run_id} — log incomplete/malformed: {log_path.name}")
                continue

            # Sanity check: variant in log must match manifest
            if parsed["variant"] != build_info["variant"]:
                skipped_variant_mismatch.append(f"{exp_id} run{run_id}")
                print(
                    f"  [WARN] {exp_id} run{run_id} — variant mismatch: "
                    f"log={parsed['variant']} manifest={build_info['variant']}"
                )
                continue

            # Compute derived values
            peak_stack = parsed["peak_stack_bytes"]
            static_ram = build_info["static_ram_bytes"]
            peak_total_ram = static_ram + peak_stack  # authoritative total RAM footprint

            verification_status = "PASS" if parsed["decap_ok"] == 1 else "FAIL"
            log_sha256 = sha256_file(log_path)

            row = {
                "experiment_id": exp_id,
                "run_id": run_id,
                "measurement_type": "renode_simulation",
                "mcu": build_info["mcu_model"],
                "board_model": build_info["board_model"],
                "core": build_info["core_arch"],
                "configured_clock_mhz": build_info["clock_mhz"],
                "variant": parsed["variant"],
                "opt_level": build_info["opt_level"],
                "iteration_count": 5,
                # Timer ticks: in this firmware the hardware timer IS configured in µs,
                # so ticks == µs at the configured clock.
                "keygen_timer_ticks": parsed["keygen_cycles"],
                "keygen_us": parsed["keygen_us"],
                "encap_timer_ticks": parsed["encap_cycles"],
                "encap_us": parsed["encap_us"],
                "decap_timer_ticks": parsed["decap_cycles"],
                "decap_us": parsed["decap_us"],
                "keygen_stddev_us": parsed["keygen_stddev"],
                "encap_stddev_us": parsed["encap_stddev"],
                "decap_stddev_us": parsed["decap_stddev"],
                "hardware_cycle_count_or_na": "N/A",
                "estimated_cycles_or_na": (
                    f"{parsed['keygen_cycles']}|"
                    f"{parsed['encap_cycles']}|"
                    f"{parsed['decap_cycles']}"
                ),
                "text_bytes": build_info["text_bytes"],
                "rodata_bytes": build_info["rodata_bytes"],
                "data_bytes": build_info["data_bytes"],
                "bss_bytes": build_info["bss_bytes"],
                "flash_bytes": build_info["flash_bytes"],
                "static_ram_bytes": static_ram,
                "peak_stack_bytes_or_na": peak_stack,
                "peak_total_ram_bytes": peak_total_ram,
                "verification_status": verification_status,
                "run_status": "SUCCESS",
                "compiler_version": build_info["compiler_version"],
                "renode_version": renode_version,
                "source_revision": source_revision,
                "elf_sha256": build_info["elf_sha256"],
                "raw_log_file": log_path.name,
                "raw_log_sha256": log_sha256,
                "timestamp_utc": timestamp,
            }
            rows.append(row)
            total_lat = parsed["keygen_us"] + parsed["encap_us"] + parsed["decap_us"]
            print(
                f"  [OK]   {exp_id:<42} run{run_id} "
                f"{parsed['variant']:<12} "
                f"{total_lat:>7} us total  "
                f"flash={build_info['flash_bytes']:>6} B  "
                f"ram={peak_total_ram:>6} B  "
                f"{verification_status}"
            )


    # Sort rows for deterministic output: target -> variant -> opt_level -> run_id
    opt_order = {"-O0": 0, "-O1": 1, "-O2": 2, "-O3": 3, "-Os": 4}
    rows.sort(key=lambda r: (
        r["mcu"], r["variant"], opt_order.get(str(r["opt_level"]), 99), r["run_id"]
    ))

    # ------------------------------------------------------------------
    # Validate arithmetic invariants before writing
    # ------------------------------------------------------------------
    arith_errors: list[str] = []
    pass_count = 0
    for r in rows:
        flash_calc = int(r["text_bytes"]) + int(r["rodata_bytes"]) + int(r["data_bytes"])
        if flash_calc != int(r["flash_bytes"]):
            arith_errors.append(
                f"{r['experiment_id']}: flash arithmetic: "
                f"{r['text_bytes']}+{r['rodata_bytes']}+{r['data_bytes']} "
                f"= {flash_calc} != {r['flash_bytes']}"
            )
        ram_calc = int(r["data_bytes"]) + int(r["bss_bytes"])
        if ram_calc != int(r["static_ram_bytes"]):
            arith_errors.append(
                f"{r['experiment_id']}: RAM arithmetic: "
                f"{r['data_bytes']}+{r['bss_bytes']} "
                f"= {ram_calc} != {r['static_ram_bytes']}"
            )
        if r["verification_status"] == "PASS":
            pass_count += 1

    # ------------------------------------------------------------------
    # Print summary
    # ------------------------------------------------------------------
    print()
    print("=" * 72)
    print(f"  SUMMARY")
    print(f"  Rows ingested              : {len(rows)}")
    print(f"  Rows passing verification  : {pass_count}")
    print(f"  Skipped (build failed)     : {len(skipped_build_failed)}")
    print(f"  Skipped (no log found)     : {len(skipped_no_log)}")
    print(f"  Skipped (parse failed)     : {len(skipped_parse_fail)}")
    print(f"  Skipped (variant mismatch) : {len(skipped_variant_mismatch)}")
    if arith_errors:
        print(f"  Arithmetic errors          : {len(arith_errors)}")
        for e in arith_errors:
            print(f"    {e}")
    print("=" * 72)

    if not rows:
        raise SystemExit("[ERROR] No rows were produced. Check log files and build manifest.")

    if args.dry_run:
        print("[DRY RUN] No files written.")
        return

    # ------------------------------------------------------------------
    # Write CSV
    # ------------------------------------------------------------------
    with DATASET_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n[DONE] Wrote {len(rows)} rows -> {DATASET_PATH}")

    # ------------------------------------------------------------------
    # Write validation report
    # ------------------------------------------------------------------
    report = {
        "status": "PASSED" if not arith_errors else "ARITHMETIC_ERRORS",
        "generated_at_utc": timestamp,
        "total_rows": len(rows),
        "pass_rows": pass_count,
        "fail_rows": len(rows) - pass_count,
        "skipped_build_failed": len(skipped_build_failed),
        "skipped_no_log": len(skipped_no_log),
        "skipped_parse_failed": len(skipped_parse_fail),
        "skipped_variant_mismatch": len(skipped_variant_mismatch),
        "arithmetic_errors": arith_errors,
        "experiment_ids": [r["experiment_id"] for r in rows],
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[DONE] Wrote validation report -> {REPORT_PATH}")
    print()


if __name__ == "__main__":
    main()
