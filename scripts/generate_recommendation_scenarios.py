#!/usr/bin/env python3
"""
generate_recommendation_scenarios.py — Derive labelled deployment scenarios.

Creates dataset/recommendation_scenarios.csv from the validated Renode benchmark
measurements. Each scenario represents a hypothetical IoT deployment context
described purely by hardware constraints (RAM budget, Flash budget, security
requirement, latency budget, MCU). The recommended variant is determined by a
deterministic rule engine: fastest feasible option that satisfies all constraints.

This dataset is used to train the AI recommendation classifier (train_recommender.py).
The measurement_type column is 'derived_recommendation_scenario' to clearly
distinguish these rows from direct Renode measurements.
"""
from __future__ import annotations

import csv
import hashlib
import itertools
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "dataset" / "benchmark_renode_measurements.csv"
DEST = ROOT / "dataset" / "recommendation_scenarios.csv"

# NIST FIPS 203 security categories
SECURITY_CATEGORY = {
    "ML-KEM-512":  1,
    "ML-KEM-768":  3,
    "ML-KEM-1024": 5,
}

FIELDS = [
    "scenario_id",
    "measurement_type",
    "source_experiment_ids",
    "mcu",
    "configured_clock_mhz",
    "available_ram_bytes",
    "available_flash_bytes",
    "security_category",
    "latency_budget_us",
    "recommended_variant",
    "decision_reason",
    "source_measurement_hash",
]

# Realistic IoT deployment RAM budgets (bytes)
RAM_VALUES = sorted({
    4_096, 8_192, 12_288, 16_384,
    24_576, 32_768, 49_152, 65_536,
    98_304, 131_072, 196_608, 262_144,
    524_288, 1_048_576,
})

# Realistic Flash budgets (bytes)
FLASH_VALUES = sorted({
    32_768, 49_152, 65_536, 98_304,
    131_072, 196_608, 262_144, 524_288,
    1_048_576, 2_097_152,
})

# Latency budgets: 0 = unlimited
LATENCY_BUDGETS_US = (0, 2_000, 5_000, 10_000, 25_000, 50_000, 100_000, 250_000)

# Minimum NIST security categories to evaluate
SECURITY_CATS = (1, 3, 5)


def _peak_total_ram(row: dict) -> int:
    """Compute peak RAM from CSV row, handling N/A gracefully."""
    try:
        v = row.get("peak_total_ram_bytes", "")
        if str(v) not in ("", "N/A"):
            return int(v)
    except (ValueError, TypeError):
        pass
    try:
        stack = row.get("peak_stack_bytes_or_na", "")
        if str(stack) in ("", "N/A"):
            return int(row["static_ram_bytes"])
        return int(row["static_ram_bytes"]) + int(stack)
    except (ValueError, TypeError):
        return int(row["static_ram_bytes"])


def main() -> None:
    # Load only verified, successful benchmark rows
    with SOURCE.open(encoding="utf-8") as fh:
        all_rows = [
            r for r in csv.DictReader(fh)
            if r.get("run_status") == "SUCCESS"
            and r.get("verification_status") == "PASS"
        ]

    if not all_rows:
        raise SystemExit(
            "[ERROR] No validated PASS measurements in source dataset.\n"
            "Run:  python scripts/rebuild_dataset_from_logs.py"
        )

    # Group observations by (MCU, clock_mhz) — the hardware identity
    groups: dict[tuple[str, str], list[dict]] = {}
    for r in all_rows:
        key = (r["mcu"], r["configured_clock_mhz"])
        groups.setdefault(key, []).append(r)

    print(f"Loaded {len(all_rows)} source measurements across {len(groups)} MCU×clock groups")
    for (mcu, clk), obs in sorted(groups.items()):
        print(f"  {mcu} @ {clk} MHz : {len(obs)} observations")

    scenarios: list[dict] = []

    for (mcu, clock), observations in groups.items():
        for ram, flash, security, budget in itertools.product(
            RAM_VALUES, FLASH_VALUES, SECURITY_CATS, LATENCY_BUDGETS_US
        ):
            candidates: list[tuple[int, int, dict]] = []

            for obs in observations:
                var = obs["variant"]
                sec_cat = SECURITY_CATEGORY.get(var, 0)

                # Security gate
                if sec_cat < security:
                    continue

                peak_ram = _peak_total_ram(obs)
                flash_needed = int(obs["flash_bytes"])
                total_lat = int(obs["keygen_us"]) + int(obs["encap_us"]) + int(obs["decap_us"])

                # Hardware constraint gates
                if peak_ram > ram:
                    continue
                if flash_needed > flash:
                    continue
                if budget > 0 and total_lat > budget:
                    continue

                # (total_latency, -security_category) — prefer faster, then higher security
                candidates.append((total_lat, -sec_cat, obs))

            candidates.sort(key=lambda item: (item[0], item[1]))
            selected_obs = candidates[0][2] if candidates else None
            source_ids = "|".join(
                sorted({obs["experiment_id"] for _, _, obs in candidates})
            ) if candidates else ""

            payload = f"{mcu}|{clock}|{ram}|{flash}|{security}|{budget}|{source_ids}"
            scenario_hash = hashlib.sha256(payload.encode()).hexdigest()

            scenarios.append({
                "scenario_id": "SCN-" + scenario_hash[:16],
                "measurement_type": "derived_recommendation_scenario",
                "source_experiment_ids": source_ids,
                "mcu": mcu,
                "configured_clock_mhz": clock,
                "available_ram_bytes": ram,
                "available_flash_bytes": flash,
                "security_category": security,
                "latency_budget_us": budget,
                "recommended_variant": (
                    selected_obs["variant"] if selected_obs else "UNSUPPORTED"
                ),
                "decision_reason": (
                    "fastest observed feasible variant"
                    if selected_obs
                    else "no observed configuration meets all constraints"
                ),
                "source_measurement_hash": scenario_hash,
            })

    with DEST.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(scenarios)

    supported = sum(1 for s in scenarios if s["recommended_variant"] != "UNSUPPORTED")
    print(
        f"\n[DONE] Wrote {len(scenarios):,} derived scenarios -> {DEST}\n"
        f"  Supported (variant assigned) : {supported:,}\n"
        f"  Unsupported (no fit)         : {len(scenarios) - supported:,}"
    )


if __name__ == "__main__":
    main()
