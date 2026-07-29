#!/usr/bin/env python3
"""
scripts/run_renode_parallel.py — Parallel Renode Benchmark Simulation Suite

Runs Renode hardware simulations in parallel across multiple CPU workers to speed up
dataset generation by 5x-8x. Each experiment binary is loaded into Renode, captured
via UART log, validated, and appended to the authentic measurement dataset.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "firmware" / "builds" / "build_manifest.json"
DATASET = ROOT / "dataset" / "benchmark_renode_measurements.csv"
LOGS = ROOT / "dataset" / "raw_logs"

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

UART = {
    "stm32f0": "usart2",
    "stm32f4": "usart2",
    "stm32h7": "usart3",
}

_DATA_RE = re.compile(
    r"^(ML-KEM-(?:512|768|1024)),"
    r"(\d+),(\d+),(\d+),"
    r"(\d+),(\d+),(\d+),"
    r"(\d+),(\d+),(\d+),"
    r"([01]),"
    r"(\d+)$",
    re.MULTILINE,
)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def parse_log(log: Path) -> dict | None:
    if not log.exists():
        return None
    for _ in range(20):
        try:
            text = log.read_text(encoding="utf-8", errors="replace")
            break
        except PermissionError:
            time.sleep(0.2)
    else:
        return None

    if "BENCHMARK SUITE COMPLETE!" not in text:
        return None

    m = _DATA_RE.search(text)
    if m is None:
        return None

    (
        variant,
        kg_cyc, enc_cyc, dec_cyc,
        kg_us, enc_us, dec_us,
        kg_std, enc_std, dec_std,
        ok,
        peak_stack,
    ) = m.groups()

    return {
        "variant": variant,
        "keygen_cycles": int(kg_cyc),
        "encap_cycles": int(enc_cyc),
        "decap_cycles": int(dec_cyc),
        "keygen_us": int(kg_us),
        "encap_us": int(enc_us),
        "decap_us": int(dec_us),
        "keygen_stddev": int(kg_std),
        "encap_stddev": int(enc_std),
        "decap_stddev": int(dec_std),
        "decap_ok": int(ok),
        "peak_stack_bytes": int(peak_stack),
    }


def run_single_simulation(
    exp_id: str,
    info: dict,
    run_id: int,
    port: int,
    run_seconds: float,
    skip_existing: bool,
    force: bool,
    renode_ver: str,
) -> dict | None:
    log = LOGS / f"{exp_id}_run{run_id:03d}.txt"
    resc = LOGS / f"{exp_id}_run{run_id:03d}.resc"

    if log.exists():
        if skip_existing:
            parsed = parse_log(log)
            if parsed:
                # Return parsed row from existing log
                peak_stack = parsed["peak_stack_bytes"]
                static_ram = info["static_ram_bytes"]
                return {
                    "experiment_id": exp_id,
                    "run_id": run_id,
                    "measurement_type": "renode_simulation",
                    "mcu": info["mcu_model"],
                    "board_model": info["board_model"],
                    "core": info["core_arch"],
                    "configured_clock_mhz": info["clock_mhz"],
                    "variant": parsed["variant"],
                    "opt_level": info["opt_level"],
                    "iteration_count": 5,
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
                    "estimated_cycles_or_na": f"{parsed['keygen_cycles']}|{parsed['encap_cycles']}|{parsed['decap_cycles']}",
                    "text_bytes": info["text_bytes"],
                    "rodata_bytes": info["rodata_bytes"],
                    "data_bytes": info["data_bytes"],
                    "bss_bytes": info["bss_bytes"],
                    "flash_bytes": info["flash_bytes"],
                    "static_ram_bytes": static_ram,
                    "peak_stack_bytes_or_na": peak_stack,
                    "peak_total_ram_bytes": static_ram + peak_stack,
                    "verification_status": "PASS" if parsed["decap_ok"] == 1 else "FAIL",
                    "run_status": "SUCCESS",
                    "compiler_version": info["compiler_version"],
                    "renode_version": renode_ver,
                    "source_revision": "unversioned-worktree",
                    "elf_sha256": info["elf_sha256"],
                    "raw_log_file": log.name,
                    "raw_log_sha256": digest(log),
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                }
        elif not force:
            return None

    uart = UART.get(info["target"], "usart2")
    resc.write_text(
        f'mach create "bench"\n'
        f'machine LoadPlatformDescription @{info["board_model"]}\n'
        f'sysbus LoadELF @{Path(info["elf_path"]).as_posix()}\n'
        f'{uart} CreateFileBackend @{log.as_posix()} true\n'
        f'start\n',
        encoding="utf-8",
    )

    process = subprocess.Popen(
        ["renode", "--disable-gui", "--hide-analyzers", "-p", "--port", str(port), "-e", f"s @{resc}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    deadline = time.monotonic() + run_seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            break
        time.sleep(0.25)
    if process.poll() is None:
        process.kill()

    process.communicate()
    resc.unlink(missing_ok=True)

    parsed = parse_log(log)
    if not parsed:
        return None

    peak_stack = parsed["peak_stack_bytes"]
    static_ram = info["static_ram_bytes"]

    return {
        "experiment_id": exp_id,
        "run_id": run_id,
        "measurement_type": "renode_simulation",
        "mcu": info["mcu_model"],
        "board_model": info["board_model"],
        "core": info["core_arch"],
        "configured_clock_mhz": info["clock_mhz"],
        "variant": parsed["variant"],
        "opt_level": info["opt_level"],
        "iteration_count": 5,
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
        "estimated_cycles_or_na": f"{parsed['keygen_cycles']}|{parsed['encap_cycles']}|{parsed['decap_cycles']}",
        "text_bytes": info["text_bytes"],
        "rodata_bytes": info["rodata_bytes"],
        "data_bytes": info["data_bytes"],
        "bss_bytes": info["bss_bytes"],
        "flash_bytes": info["flash_bytes"],
        "static_ram_bytes": static_ram,
        "peak_stack_bytes_or_na": peak_stack,
        "peak_total_ram_bytes": static_ram + peak_stack,
        "verification_status": "PASS" if parsed["decap_ok"] == 1 else "FAIL",
        "run_status": "SUCCESS",
        "compiler_version": info["compiler_version"],
        "renode_version": renode_ver,
        "source_revision": "unversioned-worktree",
        "elf_sha256": info["elf_sha256"],
        "raw_log_file": log.name,
        "raw_log_sha256": digest(log),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Parallel Renode Benchmark Runner")
    ap.add_argument("--workers", type=int, default=6, help="Number of parallel workers (default: 6)")
    ap.add_argument("--repetitions", type=int, default=1, help="Number of runs per experiment")
    ap.add_argument("--skip-existing", action="store_true", help="Skip running if valid log exists")
    ap.add_argument("--force", action="store_true", help="Overwrite existing logs")
    ap.add_argument("--run-seconds", type=float, default=25.0, help="Timeout in seconds per run (default: 25)")
    args = ap.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    builds: dict[str, dict] = manifest["builds"]
    LOGS.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print(f"  PARALLEL RENODE BENCHMARK RUNNER ({args.workers} Parallel Workers)")
    print(f"  Total Registered Experiments: {len(builds)}")
    print("=" * 72)

    tasks = []
    base_port = 20000
    idx = 0

    for exp_id, info in builds.items():
        if info.get("build_status") != "SUCCESS":
            continue
        for run_id in range(1, args.repetitions + 1):
            port = base_port + (idx % 1000)
            idx += 1
            tasks.append((exp_id, info, run_id, port))

    results: list[dict] = []
    start_t = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                run_single_simulation,
                exp_id,
                info,
                run_id,
                port,
                args.run_seconds,
                args.skip_existing,
                args.force,
                "Renode v1.16.1",
            ): (exp_id, run_id)
            for exp_id, info, run_id, port in tasks
        }

        completed_cnt = 0
        total_cnt = len(futures)

        for future in as_completed(futures):
            exp_id, run_id = futures[future]
            completed_cnt += 1
            try:
                row = future.result()
                if row:
                    results.append(row)
                    lat = row['keygen_us'] + row['encap_us'] + row['decap_us']
                    print(f"[{completed_cnt:>3}/{total_cnt}] [OK]   {exp_id:<40} run{run_id} ({lat} us)", flush=True)
                else:
                    print(f"[{completed_cnt:>3}/{total_cnt}] [FAIL] {exp_id:<40} run{run_id}", flush=True)
            except Exception as e:
                print(f"[{completed_cnt:>3}/{total_cnt}] [ERR]  {exp_id:<40} run{run_id}: {e}", flush=True)

    elapsed = time.time() - start_t
    results.sort(key=lambda r: (r["mcu"], r["variant"], r["opt_level"], r["run_id"]))

    with DATASET.open("w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(results)

    print()
    print("=" * 72)
    print(f"  PARALLEL SIMULATION COMPLETE in {elapsed:.1f} seconds!")
    print(f"  Successfully collected dataset rows: {len(results)} / {total_cnt}")
    print(f"  Dataset saved -> {DATASET}")
    print("=" * 72)


if __name__ == "__main__":
    main()
