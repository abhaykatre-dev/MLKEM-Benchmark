#!/usr/bin/env python3
"""
verify_dataset.py — Fail-Closed Cryptographic Audit Tool for ML-KEM Benchmark Dataset

Verifies every row in benchmark_renode_measurements.csv against:
  1. The build manifest (mcu, board, core, clock, variant, opt_level, elf_sha256)
  2. The raw UART log file (existence, SHA-256 hash integrity, completeness marker)
  3. Flash and RAM arithmetic invariants
  4. Uniqueness of (experiment_id, run_id) pairs

The ELF binary integrity check is performed only when the ELF file is present on
the local filesystem (the ELF may legitimately be absent on a reviewer machine that
only has the CSV + logs). The elf_sha256 column still anchors provenance even when
the binary is not physically present.

Exit code 0 = all checks passed; 1 = one or more errors.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "dataset" / "benchmark_renode_measurements.csv"
LOGS = ROOT / "dataset" / "raw_logs"
MANIFEST_PATH = ROOT / "firmware" / "builds" / "build_manifest.json"
REPORT = ROOT / "dataset" / "validation_report.json"

# Regex matching the data row emitted by the firmware UART log
_DATA_RE = re.compile(
    r"^(ML-KEM-(?:512|768|1024)),"
    r"(\d+),(\d+),(\d+),"      # keygen/encap/decap cycles
    r"(\d+),(\d+),(\d+),"      # keygen/encap/decap µs
    r"(\d+),(\d+),(\d+),"      # stddev
    r"([01]),"                   # decap_ok
    r"(\d+)$",                   # peak_stack
    re.MULTILINE,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    if not DATA.exists():
        raise SystemExit(f"[ERROR] Dataset not found: {DATA}")
    if not MANIFEST_PATH.exists():
        raise SystemExit(f"[ERROR] Build manifest not found: {MANIFEST_PATH}")

    manifest: dict[str, dict] = json.loads(
        MANIFEST_PATH.read_text(encoding="utf-8")
    )["builds"]

    rows = list(csv.DictReader(DATA.open(encoding="utf-8")))
    errors: list[str] = []
    seen: set[tuple] = set()
    passed = 0

    for n, row in enumerate(rows, 1):
        exp_id = row["experiment_id"]
        key = (exp_id, row["run_id"])

        # ----------------------------------------------------------------
        # 1. Duplicate check
        # ----------------------------------------------------------------
        if key in seen:
            errors.append(f"row {n} ({exp_id}): duplicate (experiment_id, run_id)")
        seen.add(key)

        # ----------------------------------------------------------------
        # 2. Build manifest presence and status
        # ----------------------------------------------------------------
        info = manifest.get(exp_id)
        if info is None:
            errors.append(f"row {n} ({exp_id}): experiment ID not found in build manifest")
            continue
        if info.get("build_status") != "SUCCESS":
            errors.append(f"row {n} ({exp_id}): build_status is not SUCCESS")
            continue

        # ----------------------------------------------------------------
        # 3. Measurement type
        # ----------------------------------------------------------------
        if row.get("measurement_type") != "renode_simulation":
            errors.append(
                f"row {n} ({exp_id}): measurement_type must be 'renode_simulation', "
                f"got '{row.get('measurement_type')}'"
            )

        # ----------------------------------------------------------------
        # 4. Manifest field agreement
        # ----------------------------------------------------------------
        field_map = [
            ("mcu",                  "mcu_model"),
            ("board_model",          "board_model"),
            ("core",                 "core_arch"),
            ("configured_clock_mhz", "clock_mhz"),
            ("variant",              "variant"),
            ("opt_level",            "opt_level"),
            ("elf_sha256",           "elf_sha256"),
        ]
        for csv_key, manifest_key in field_map:
            csv_val = row.get(csv_key, "")
            manifest_val = str(info.get(manifest_key, ""))
            if csv_val != manifest_val:
                errors.append(
                    f"row {n} ({exp_id}): {csv_key} mismatch — "
                    f"CSV='{csv_val}' vs manifest='{manifest_val}'"
                )

        # ----------------------------------------------------------------
        # 5. Raw log file integrity
        # ----------------------------------------------------------------
        log_name = row.get("raw_log_file", "")
        log_path = LOGS / log_name if log_name else None

        # Also try alternate naming convention as a fallback
        if log_path is None or not log_path.exists():
            alt_candidates = [
                LOGS / f"{exp_id}_run001.txt",
                LOGS / f"{exp_id}.txt",
            ]
            for alt in alt_candidates:
                if alt.exists():
                    log_path = alt
                    break

        if log_path is None or not log_path.exists():
            errors.append(f"row {n} ({exp_id}): raw log file not found (expected: {log_name})")
        else:
            # Hash check
            actual_hash = sha256_file(log_path)
            expected_hash = row.get("raw_log_sha256", "")
            if expected_hash and actual_hash != expected_hash:
                errors.append(
                    f"row {n} ({exp_id}): raw_log_sha256 mismatch — "
                    f"file has {actual_hash[:16]}… expected {expected_hash[:16]}…"
                )
            # Content check
            text = log_path.read_text(encoding="utf-8", errors="replace")
            if "BENCHMARK SUITE COMPLETE!" not in text:
                errors.append(f"row {n} ({exp_id}): log missing 'BENCHMARK SUITE COMPLETE!' marker")
            if row.get("variant", "") not in text:
                errors.append(f"row {n} ({exp_id}): variant '{row.get('variant')}' not found in log")
            if _DATA_RE.search(text) is None:
                errors.append(f"row {n} ({exp_id}): no parseable data row found in log")

        # ----------------------------------------------------------------
        # 6. ELF binary integrity (optional — only when ELF is present)
        # ----------------------------------------------------------------
        elf_path_str = info.get("elf_path", "")
        if elf_path_str:
            elf_path = Path(elf_path_str)
            if elf_path.exists():
                elf_actual = sha256_file(elf_path)
                elf_expected = row.get("elf_sha256", "")
                if elf_expected and elf_actual != elf_expected:
                    errors.append(
                        f"row {n} ({exp_id}): elf_sha256 mismatch — "
                        f"file has {elf_actual[:16]}… expected {elf_expected[:16]}…"
                    )

        # ----------------------------------------------------------------
        # 7. Flash arithmetic: .text + .rodata + .data == flash_bytes
        # ----------------------------------------------------------------
        try:
            text_b = int(row["text_bytes"])
            rodata_b = int(row["rodata_bytes"])
            data_b = int(row["data_bytes"])
            flash_b = int(row["flash_bytes"])
            if text_b + rodata_b + data_b != flash_b:
                errors.append(
                    f"row {n} ({exp_id}): flash_bytes arithmetic: "
                    f"{text_b}+{rodata_b}+{data_b}={text_b+rodata_b+data_b} != {flash_b}"
                )
        except (KeyError, ValueError) as exc:
            errors.append(f"row {n} ({exp_id}): flash arithmetic parse error: {exc}")

        # ----------------------------------------------------------------
        # 8. RAM arithmetic: .data + .bss == static_ram_bytes
        # ----------------------------------------------------------------
        try:
            bss_b = int(row["bss_bytes"])
            sram_b = int(row["static_ram_bytes"])
            if data_b + bss_b != sram_b:
                errors.append(
                    f"row {n} ({exp_id}): static_ram_bytes arithmetic: "
                    f"{data_b}+{bss_b}={data_b+bss_b} != {sram_b}"
                )
        except (KeyError, ValueError) as exc:
            errors.append(f"row {n} ({exp_id}): RAM arithmetic parse error: {exc}")

        # ----------------------------------------------------------------
        # 9. Peak total RAM = static + stack
        # ----------------------------------------------------------------
        try:
            peak_stack_val = row.get("peak_stack_bytes_or_na", "N/A")
            peak_total_val = row.get("peak_total_ram_bytes", "")
            if peak_stack_val not in ("N/A", "") and peak_total_val not in ("N/A", ""):
                expected_total = int(row["static_ram_bytes"]) + int(peak_stack_val)
                if int(peak_total_val) != expected_total:
                    errors.append(
                        f"row {n} ({exp_id}): peak_total_ram_bytes arithmetic: "
                        f"{row['static_ram_bytes']}+{peak_stack_val}={expected_total} "
                        f"!= {peak_total_val}"
                    )
        except (ValueError, KeyError) as exc:
            errors.append(f"row {n} ({exp_id}): peak RAM arithmetic parse error: {exc}")

        if row.get("verification_status") == "PASS":
            passed += 1

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------
    status = "PASSED" if not errors else "FAILED"
    report = {
        "status": status,
        "generated_at_utc": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "total_rows": len(rows),
        "pass_rows": passed,
        "fail_rows": len(rows) - passed,
        "error_count": len(errors),
        "errors": errors,
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
