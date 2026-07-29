#!/usr/bin/env python3
"""
run_renode_simulations.py — Run manifest ELFs in Renode and collect direct measurements.

This script iterates over the build manifest, launches each ELF inside Renode,
waits for the firmware's UART benchmark output, parses the structured CSV data
line, and appends a fully-audited row to benchmark_renode_measurements.csv.

Every row produced by this script is cryptographically anchored:
  - elf_sha256      : SHA-256 of the compiled ELF binary
  - raw_log_sha256  : SHA-256 of the captured UART log text file
  - peak_total_ram_bytes : static_ram_bytes + peak_stack_bytes (computed, not simulated)

Usage:
    python scripts/run_renode_simulations.py [--target stm32f4] [--repetitions 3]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import time
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

# UART peripheral per target family
UART = {
    "stm32f0": "usart2",
    "stm32f4": "usart2",
    "stm32h7": "usart3",
    "nrf52840": "uart0",
    "hifive1": "uart0",
}

# Regex matching the firmware's CSV output line
_DATA_RE = re.compile(
    r"^(ML-KEM-(?:512|768|1024)),"   # variant
    r"(\d+),(\d+),(\d+),"             # keygen/encap/decap cycles
    r"(\d+),(\d+),(\d+),"             # keygen/encap/decap µs
    r"(\d+),(\d+),(\d+),"             # stddev µs
    r"([01]),"                          # decap_ok
    r"(\d+)$",                          # peak_stack_bytes
    re.MULTILINE,
)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def renode_version() -> str:
    result = subprocess.run(["renode", "--version"], capture_output=True, text=True)
    if result.returncode == 0:
        return (result.stdout or result.stderr).strip().splitlines()[0]
    return "unknown"


def create_resc(info: dict, log: Path, script: Path) -> None:
    uart = UART.get(info["target"], "uart0")
    script.write_text(
        f'mach create "bench"\n'
        f'machine LoadPlatformDescription @{info["board_model"]}\n'
        f'sysbus LoadELF @{Path(info["elf_path"]).as_posix()}\n'
        f'{uart} CreateFileBackend @{log.as_posix()} true\n'
        f'start\n',
        encoding="utf-8",
    )


def parse_log(log: Path) -> dict | None:
    """Parse UART log; retry briefly for file lock release."""
    for _ in range(40):
        try:
            text = log.read_text(encoding="utf-8", errors="replace")
            break
        except PermissionError:
            time.sleep(0.25)
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


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Run manifest ELFs in Renode and collect direct benchmark measurements."
    )
    ap.add_argument("--repetitions", type=int, default=1,
                    help="Number of Renode runs per experiment (default: 1)")
    ap.add_argument("--force", action="store_true",
                    help="Overwrite existing raw log files")
    ap.add_argument("--skip-existing", action="store_true",
                    help="Skip running simulation if a valid raw log file already exists")
    ap.add_argument("--append-dataset", action="store_true",
                    help="Preserve rows for experiments NOT run in this invocation")
    ap.add_argument("--run-seconds", type=float, default=120.0,
                    help="Seconds to wait for Renode output before timing out (default: 120)")
    ap.add_argument("--experiment", action="append",
                    help="Run only this exact manifest experiment ID (repeatable)")
    ap.add_argument("--skip-experiment", action="append", default=[],
                    help="Skip this experiment ID even if it is in the manifest")
    ap.add_argument("--target", choices=sorted(UART), action="append",
                    help="Only run experiments for this target family (repeatable)")
    args = ap.parse_args()

    if args.repetitions < 1:
        raise SystemExit("--repetitions must be >= 1")
    if shutil.which("renode") is None:
        raise SystemExit("Renode must be on PATH. Install from https://renode.io/")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    builds: dict[str, dict] = manifest["builds"]
    LOGS.mkdir(parents=True, exist_ok=True)

    rnode_ver = renode_version()
    rows: list[dict] = []

    for exp_id, info in sorted(builds.items()):
        if args.experiment and exp_id not in args.experiment:
            continue
        if exp_id in args.skip_experiment:
            continue
        if args.target and info.get("target") not in args.target:
            continue
        if info.get("build_status") != "SUCCESS":
            print(f"  [SKIP] {exp_id} — build_status={info.get('build_status')}")
            continue

        for run_id in range(1, args.repetitions + 1):
            log = LOGS / f"{exp_id}_run{run_id:03d}.txt"
            resc = LOGS / f"{exp_id}_run{run_id:03d}.resc"

            if log.exists():
                if args.skip_existing:
                    parsed_existing = parse_log(log)
                    if parsed_existing:
                        print(f"  [SKIP EXISTING] {exp_id} run {run_id}")
                        continue
                elif not args.force:
                    raise SystemExit(
                        f"Refusing to overwrite existing log: {log}\n"
                        f"Archive it first, or pass --force or --skip-existing."
                    )


            create_resc(info, log, resc)

            # Use a deterministic port derived from experiment ID to avoid collisions
            monitor_port = str(
                20000 + (int(hashlib.sha256(exp_id.encode()).hexdigest()[:6], 16) % 20000)
            )
            process = subprocess.Popen(
                ["renode", "--disable-gui", "--hide-analyzers", "-p",
                 "--port", monitor_port, "-e", f"s @{resc}"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )

            deadline = time.monotonic() + args.run_seconds
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    break
                time.sleep(0.25)
            if process.poll() is None:
                process.kill()

            try:
                stdout, stderr = process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()

            parsed = parse_log(log) if log.exists() else None
            if not parsed:
                (LOGS / f"{exp_id}_run{run_id:03d}.renode-stdout.txt").write_text(
                    stdout, encoding="utf-8", errors="replace"
                )
                (LOGS / f"{exp_id}_run{run_id:03d}.renode-stderr.txt").write_text(
                    stderr, encoding="utf-8", errors="replace"
                )
                print(f"  [FAIL] {exp_id} run {run_id}  exit={process.returncode}")
                continue

            resc.unlink(missing_ok=True)

            if parsed["variant"] != info["variant"]:
                raise SystemExit(
                    f"Variant mismatch in {log}: "
                    f"log={parsed['variant']} manifest={info['variant']}"
                )

            peak_stack = parsed["peak_stack_bytes"]
            static_ram = info["static_ram_bytes"]
            peak_total_ram = static_ram + peak_stack

            rows.append({
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
                "estimated_cycles_or_na": (
                    f"{parsed['keygen_cycles']}|"
                    f"{parsed['encap_cycles']}|"
                    f"{parsed['decap_cycles']}"
                ),
                "text_bytes": info["text_bytes"],
                "rodata_bytes": info["rodata_bytes"],
                "data_bytes": info["data_bytes"],
                "bss_bytes": info["bss_bytes"],
                "flash_bytes": info["flash_bytes"],
                "static_ram_bytes": static_ram,
                "peak_stack_bytes_or_na": peak_stack,
                "peak_total_ram_bytes": peak_total_ram,
                "verification_status": "PASS" if parsed["decap_ok"] == 1 else "FAIL",
                "run_status": "SUCCESS",
                "compiler_version": info["compiler_version"],
                "renode_version": rnode_ver,
                "source_revision": "unversioned-worktree",
                "elf_sha256": info["elf_sha256"],
                "raw_log_file": log.name,
                "raw_log_sha256": digest(log),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            })
            total = parsed["keygen_us"] + parsed["encap_us"] + parsed["decap_us"]
            print(f"  [OK]   {exp_id} run {run_id}  {total} µs total")

    # Optionally preserve rows from experiments not included in this run
    if args.append_dataset and DATASET.exists():
        selected = {row["experiment_id"] for row in rows}
        existing = [
            row for row in csv.DictReader(DATASET.open(encoding="utf-8"))
            if row["experiment_id"] not in selected
        ]
        rows = existing + rows

    rows.sort(key=lambda r: (r["experiment_id"], int(r["run_id"])))

    with DATASET.open("w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n[DONE] Wrote {len(rows)} rows -> {DATASET}")


if __name__ == "__main__":
    main()
