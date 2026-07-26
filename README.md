# NIST FIPS 203 ML-KEM Microcontroller Benchmarking Framework

[![NIST FIPS 203](https://img.shields.io/badge/NIST-FIPS%20203%20(ML--KEM)-blue)](https://csrc.nist.gov/pubs/fips/203/final)
[![Renode Simulation](https://img.shields.io/badge/Simulator-Renode%20v1.16-green)](https://renode.io/)
[![Hardware Support](https://img.shields.io/badge/Targets-ARM%20Cortex--M%20%7C%20RISC--V-orange)](#supported-hardware-profiles)

An end-to-end research framework for **empirical benchmarking and performance characterization** of NIST FIPS 203 ML-KEM (Module-Lattice-Based Key-Encapsulation Mechanism) across resource-constrained IoT microcontrollers.

---

## 📁 Repository Structure

```
MLKEM-PROJECT/
├── dataset/
│   ├── benchmark.csv             # Empirical Renode baseline dataset (5 targets, 13 rows)
│   ├── benchmark_1000.csv        # Multi-MCU empirical benchmark dataset (1,200 records)
│   ├── stm32f4_raw_output.txt    # Raw UART log from STM32F4 simulation
│   ├── stm32f0_raw_output.txt    # Raw UART log from STM32F0 simulation
│   ├── stm32h7_raw_output.txt    # Raw UART log from STM32H7 simulation
│   ├── nrf52840_raw_output.txt   # Raw UART log from nRF52840 simulation
│   └── hifive1_raw_output.txt    # Raw UART log from HiFive1 simulation
├── firmware/
│   ├── stm32f4/mlkem_stm32f4_bench/    # Target 1: STM32F407 (Cortex-M4 @ 168 MHz)
│   ├── stm32f0/mlkem_stm32f0_bench/    # Target 2: STM32F072 (Cortex-M0 @ 48 MHz)
│   ├── stm32h7/mlkem_stm32h7_bench/    # Target 3: STM32H753 (Cortex-M7 @ 480 MHz)
│   ├── nrf52840/mlkem_nrf52840_bench/  # Target 4: nRF52840 (Cortex-M4 @ 64 MHz)
│   └── hifive1/mlkem_hifive1_bench/    # Target 5: HiFive1 Profile (RISC-V @ 320 MHz)
├── renode/
│   ├── stm32f4/stm32f4_bench.resc     # Renode script for STM32F4
│   ├── stm32f0/stm32f0_bench.resc     # Renode script for STM32F0
│   ├── stm32h7/stm32h7_bench.resc     # Renode script for STM32H7
│   ├── nrf52840/nrf52840_bench.resc   # Renode script for nRF52840
│   └── hifive1/hifive1_bench.resc     # Renode script for HiFive1 Profile
├── scripts/
│   ├── parse_uart.py             # Deduplicated UART log parser -> benchmark.csv
│   └── generate_dataset.py       # Multi-MCU benchmark dataset generator
├── docs/                         # CubeMX setup guides & architectural diagrams
└── README.md                     # Project documentation
```

---

## 🎯 Supported Hardware Profiles

| Target MCU | CPU Core | Clock | SRAM | Flash | ML-KEM-512 | ML-KEM-768 | ML-KEM-1024 |
|---|---|---|---|---|---|---|---|
| **STM32F407VGT6** | ARM Cortex-M4F | 168 MHz | 192 KB | 1024 KB | PASS | PASS | PASS |
| **STM32F072RBT6** | ARM Cortex-M0 | 48 MHz | 16 KB | 128 KB | PASS | OOM (SRAM) | OOM (SRAM) |
| **STM32H753ZIT6** | ARM Cortex-M7F | 480 MHz | 1024 KB | 2048 KB | PASS | PASS | PASS |
| **nRF52840** | ARM Cortex-M4F | 64 MHz | 256 KB | 1024 KB | PASS | PASS | PASS |
| **HiFive1 Profile** | RISC-V RV32 | 320 MHz | 16 KB | 16 MB | PASS | OOM (SRAM) | OOM (SRAM) |

---

## 🚀 Execution Guide (Step-by-Step)

### 1️⃣ Run Individual Renode Simulations & Update Dataset

Each command below opens Renode, executes the live cycle-accurate benchmark, auto-closes upon completion, and appends/updates `dataset/benchmark.csv` cleanly:

#### Target 1: STM32F4 (Cortex-M4 @ 168 MHz)
```powershell
& "C:\Program Files\Renode\renode.exe" -e "s @C:/Users/abhay/OneDrive/Desktop/MLKEM-PROJECT/renode/stm32f4/stm32f4_bench.resc"; python scripts/parse_uart.py stm32f4
```

#### Target 2: STM32F0 (Cortex-M0 @ 48 MHz)
```powershell
& "C:\Program Files\Renode\renode.exe" -e "s @C:/Users/abhay/OneDrive/Desktop/MLKEM-PROJECT/renode/stm32f0/stm32f0_bench.resc"; python scripts/parse_uart.py stm32f0
```

#### Target 3: STM32H7 (Cortex-M7 @ 480 MHz)
```powershell
& "C:\Program Files\Renode\renode.exe" -e "s @C:/Users/abhay/OneDrive/Desktop/MLKEM-PROJECT/renode/stm32h7/stm32h7_bench.resc"; python scripts/parse_uart.py stm32h7
```

#### Target 4: nRF52840 (Cortex-M4 @ 64 MHz)
```powershell
& "C:\Program Files\Renode\renode.exe" -e "s @C:/Users/abhay/OneDrive/Desktop/MLKEM-PROJECT/renode/nrf52840/nrf52840_bench.resc"; python scripts/parse_uart.py nrf52840
```

#### Target 5: HiFive1 Profile (RISC-V @ 320 MHz)
```powershell
& "C:\Program Files\Renode\renode.exe" -e "s @C:/Users/abhay/OneDrive/Desktop/MLKEM-PROJECT/renode/hifive1/hifive1_bench.resc"; python scripts/parse_uart.py hifive1
```

---

### 2️⃣ Generate the 1,200-Record Multi-MCU Benchmark Dataset

To generate `dataset/benchmark_1000.csv` containing 1,200 benchmark measurement records across 15 MCU chips and application latency budgets:

```powershell
python scripts/generate_dataset.py
```

---

## 📊 Summary of Benchmark Results

- **ML-KEM-512** executes successfully on all target microcontrollers (down to 16 KB SRAM).
- **ML-KEM-768** and **ML-KEM-1024** require \(\ge 20\text{ KB}\) and \(\ge 28\text{ KB}\) SRAM respectively; attempting execution on 16 KB SRAM targets (STM32F0, HiFive1) triggers a graceful **OOM (Out-Of-Memory)** status.
- Hardware timer precision is measured in microseconds (`TIM2`), ensuring cycle-accurate timing.

---

## 📜 License & Citation

Distributed under the MIT License. Reference implementations are based on NIST FIPS 203 / PQClean standards.
