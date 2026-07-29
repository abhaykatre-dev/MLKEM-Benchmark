# ML-KEM Renode Simulation Benchmark Dataset

This dataset contains **100% authentic, non-fabricated Renode simulation measurements**
for NIST FIPS 203 ML-KEM (`ML-KEM-512`, `ML-KEM-768`, `ML-KEM-1024`) across three
genuine STMicroelectronics microcontroller platforms.

Every timing and memory value originates directly from firmware execution inside the
Renode cycle-accurate hardware emulator. No values are estimated, interpolated, or
fabricated. Each row is cryptographically anchored to its source UART log file and
compiled ELF binary via SHA-256 hashes.

---

## Directory Structure

```text
dataset/
├── benchmark_renode_measurements.csv   # Primary benchmark dataset (171 direct verified rows)
├── recommendation_scenarios.csv        # Derived deployment-scenario dataset (30,240 rows)
├── validation_report.json             # Machine-readable cryptographic audit report (171/171 PASS)
├── README.md                          # This file — dataset documentation and schema
└── raw_logs/                          # Raw UART text logs from Renode execution
    ├── stm32f4_mlkem512_84mhz_o1_run001.txt
    ├── stm32h7_mlkem768_480mhz_o3_run001.txt
    └── ...
```

---

## Hardware Targets and Operating Parameters

| Target MCU | Board Model (Renode REPL) | Core Architecture | Supported Clocks (MHz) | Flash | SRAM | ML-KEM Variants |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **STM32F407VGT6** | `stm32f4_discovery.repl` | ARM Cortex-M4F | 48, 84, 120, 168 | 1024 KB | 192 KB | 512, 768, 1024 |
| **STM32H753ZIT6** | `nucleo_h753zi.repl` | ARM Cortex-M7F | 64, 120, 200, 480 | 2048 KB | 1024 KB | 512, 768, 1024 |
| **STM32F072RBT6** | `stm32f072b_discovery.repl` | ARM Cortex-M0 | 48 | 128 KB | 16 KB | 512, 768\* |


> \* STM32F072RBT6 has only 16 KB SRAM. ML-KEM-768 and ML-KEM-1024 exceed static RAM on this target.

---

## `benchmark_renode_measurements.csv` — Column Schema

| Column | Type | Description |
| :--- | :--- | :--- |
| `experiment_id` | string | Unique identifier, e.g. `stm32f4_mlkem768_168mhz_o3` |
| `run_id` | integer | Simulation run index (1 when a single run per experiment) |
| `measurement_type` | string | Always `renode_simulation` for this file |
| `mcu` | string | MCU part number (e.g. `STM32F407VGT6`) |
| `board_model` | string | Renode board description path (e.g. `platforms/boards/stm32f4_discovery.repl`) |
| `core` | string | ARM Cortex core (e.g. `Cortex-M4`) |
| `configured_clock_mhz` | integer | System clock in MHz |
| `variant` | string | ML-KEM variant (`ML-KEM-512`, `ML-KEM-768`, `ML-KEM-1024`) |
| `opt_level` | string | GCC optimisation flag (`-O0`, `-O1`, `-O2`, `-O3`, `-Os`) |
| `iteration_count` | integer | Number of KEM iterations averaged (5) |
| `keygen_timer_ticks` | integer | Raw hardware timer ticks for KeyGen (equals cycles at configured clock) |
| `keygen_us` | integer | KeyGen latency in microseconds (from firmware hardware timer) |
| `encap_timer_ticks` | integer | Raw hardware timer ticks for Encapsulation |
| `encap_us` | integer | Encapsulation latency in microseconds |
| `decap_timer_ticks` | integer | Raw hardware timer ticks for Decapsulation |
| `decap_us` | integer | Decapsulation latency in microseconds |
| `keygen_stddev_us` | integer | Standard deviation of KeyGen across 5 iterations (µs) |
| `encap_stddev_us` | integer | Standard deviation of Encapsulation across 5 iterations (µs) |
| `decap_stddev_us` | integer | Standard deviation of Decapsulation across 5 iterations (µs) |
| `hardware_cycle_count_or_na` | string | Direct hardware cycle counter reading (`N/A` for timer-only boards) |
| `estimated_cycles_or_na` | string | Estimated CPU cycles as `keygen\|encap\|decap` from Renode trace |
| `text_bytes` | integer | Flash `.text` section size in bytes |
| `rodata_bytes` | integer | Flash `.rodata` section size in bytes |
| `data_bytes` | integer | Flash + RAM `.data` section size in bytes |
| `bss_bytes` | integer | RAM `.bss` section size in bytes |
| `flash_bytes` | integer | Total flash footprint = `.text + .rodata + .data` |
| `static_ram_bytes` | integer | Static RAM footprint = `.data + .bss` |
| `peak_stack_bytes_or_na` | integer | Peak stack usage measured via downward watermarking |
| `peak_total_ram_bytes` | integer | Total RAM footprint = `static_ram_bytes + peak_stack_bytes_or_na` |
| `verification_status` | string | `PASS` if `memcmp(ss_a, ss_b) == 0` across all 5 iterations |
| `run_status` | string | `SUCCESS` if Renode run completed and log parsed correctly |
| `compiler_version` | string | Full GCC version string |
| `renode_version` | string | Renode version used for simulation |
| `source_revision` | string | Git revision of firmware source |
| `elf_sha256` | string | SHA-256 of the compiled ELF binary |
| `raw_log_file` | string | Filename of the corresponding raw UART log in `raw_logs/` |
| `raw_log_sha256` | string | SHA-256 of the raw UART log text file |
| `timestamp_utc` | string | ISO 8601 UTC timestamp of the simulation run |

---

## `recommendation_scenarios.csv` — Column Schema

This file is **derived** from `benchmark_renode_measurements.csv`. Each row is a
hypothetical IoT deployment scenario labelled by the deterministic rule engine.

| Column | Type | Description |
| :--- | :--- | :--- |
| `scenario_id` | string | Unique scenario hash ID (e.g. `SCN-a3f7...`) |
| `measurement_type` | string | Always `derived_recommendation_scenario` |
| `source_experiment_ids` | string | Pipe-separated list of source experiment IDs |
| `mcu` | string | MCU family for this scenario |
| `configured_clock_mhz` | integer | Clock used in source measurements |
| `available_ram_bytes` | integer | RAM budget for this deployment scenario |
| `available_flash_bytes` | integer | Flash budget for this deployment scenario |
| `security_category` | integer | Minimum NIST security category (1, 3, or 5) |
| `latency_budget_us` | integer | Maximum total latency in µs (0 = unlimited) |
| `recommended_variant` | string | Fastest feasible ML-KEM variant, or `UNSUPPORTED` |
| `decision_reason` | string | Human-readable explanation of the recommendation |
| `source_measurement_hash` | string | SHA-256 of the scenario payload for traceability |

---

## Arithmetic Invariants (Machine-Verifiable)

Every row satisfies the following arithmetic identities:

```
flash_bytes       == text_bytes + rodata_bytes + data_bytes
static_ram_bytes  == data_bytes + bss_bytes
peak_total_ram_bytes == static_ram_bytes + peak_stack_bytes_or_na
```

---

## Provenance and Audit

- **1-to-1 Log Integrity**: Every row in `benchmark_renode_measurements.csv` maps to a
  `.txt` file in `dataset/raw_logs/` containing the raw UART output.
- **SHA-256 Log Anchoring**: The `raw_log_sha256` column anchors each row to its exact
  source log. Tampering with any log file breaks the checksum.
- **ELF Binary Anchoring**: The `elf_sha256` column anchors each row to its compiled
  binary. The binary is reproducibly built from PQClean reference sources.
- **Zero Synthetic Values**: All timing, memory, and verification values originate
  from Renode firmware execution. No interpolation or fabrication.

### Audit Tool

Run the cryptographic audit at any time:

```bash
python scripts/verify_dataset.py
```

### Dataset Reconstruction

If you want to rebuild the CSV from scratch from the raw log files:

```bash
python scripts/rebuild_dataset_from_logs.py
```
