# 🔬 ML-KEM Microcontroller Benchmarking & AI Recommendation System

A research-grade performance benchmarking suite and constraint-aware AI recommendation framework for NIST FIPS 203 Post-Quantum Cryptography (**ML-KEM-512**, **ML-KEM-768**, **ML-KEM-1024**) on ARM Cortex microcontrollers (**STM32F0**, **STM32F4**, **STM32H7**) using **Renode cycle-accurate emulators**.

---

## ✨ Features

- **100% Authentic Renode Benchmark Dataset**: 171 verified hardware simulation rows across 9 MCU clock configurations (48 MHz to 480 MHz) and 6 compiler optimization levels (`-O0`, `-O1`, `-O2`, `-O3`, `-Ofast`, `-Os`).
- **Cryptographic Provenance**: Every dataset row is anchored to its raw UART text log and compiled ELF binary via SHA-256 checksums.
- **Parallel Simulation Engine**: Multi-threaded Renode runner (`scripts/run_renode_parallel.py`) processing 154+ experiments in minutes.
- **AI & Rule-Based Recommendation Engine**: Interactive CLI and Machine Learning models to select optimal ML-KEM variants given RAM, Flash, clock, and NIST security constraints.
- **Modern Web Dashboard**: Full-stack React + TypeScript + Vite + Tailwind UI frontend for visualizing benchmark analytics, processor footprints, and AI recommendations.

---

## ⚡ Quick Start

### 1. Launch Web Frontend UI
```bash
npm --prefix frontend install
npm --prefix frontend run dev
```

### 2. Run Cryptographic Dataset Audit
```bash
python scripts/verify_dataset.py
```

### 3. Run AI Recommendation Engine (CLI)
```bash
python ai/recommend.py --mcu STM32F407VGT6 --ram 192 --flash 1024 --security 3 --latency 5000
```

### 4. Execute Parallel Renode Benchmark Suite
```bash
python scripts/register_all_elfs.py
python scripts/run_renode_parallel.py --workers 6 --skip-existing
python scripts/rebuild_dataset_from_logs.py
```

---

## 📁 Repository Structure

```text
MLKEM-PROJECT/
├── frontend/                         # Modern React + Vite + Tailwind UI
├── dataset/                          # 171 verified benchmark rows & 30,240 scenarios
│   ├── benchmark_renode_measurements.csv
│   ├── recommendation_scenarios.csv
│   └── raw_logs/                     # Raw UART serial output text logs
├── firmware/                         # STM32 C source & 169 compiled ELF binaries
│   └── builds/build_manifest.json    # Exact section sizes (.text, .rodata, .data, .bss)
├── ai/                               # Constraint-aware recommendation models & CLI tool
├── scripts/                          # Parallel Renode runners & dataset verification scripts
└── README.md                         # Project documentation
```

---

## 📜 License & Citations

Developed for Post-Quantum Cryptography microcontroller benchmarking research.
Reference implementation code sourced from **PQClean** (NIST FIPS 203 specification).
