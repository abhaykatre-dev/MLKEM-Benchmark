#!/usr/bin/env python3
"""Build one reproducible ELF per supported MCU, ML-KEM variant, and optimisation.

Only frequencies configured by the checked-in firmware are included.  A compiler
definition must never be used to pretend that a board runs at another frequency.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDS = ROOT / "firmware" / "builds"
MANIFEST = BUILDS / "build_manifest.json"
VARIANTS = ("512", "768", "1024")
OPTS = ("-O0", "-O1", "-O2", "-O3", "-Os")
TARGETS = {
    "stm32f0": dict(mcu="STM32F072RBT6", board="platforms/boards/stm32f072b_discovery.repl",
                     core="Cortex-M0", clock=48, flash_kb=128, ram_kb=16,
                     project=ROOT / "firmware/stm32f0/mlkem_stm32f0_bench",
                     linker="STM32F072RBTX_FLASH.ld", cpu=("-mcpu=cortex-m0", "-mthumb"),
                     defines=("-DDEBUG", "-DUSE_HAL_DRIVER", "-DSTM32F072xB")),
    "stm32f4": dict(mcu="STM32F407VGT6", board="platforms/boards/stm32f4_discovery.repl",
                     core="Cortex-M4", clock=168, flash_kb=1024, ram_kb=192,
                     project=ROOT / "firmware/stm32f4/mlkem_stm32f4_bench",
                     linker="STM32F407VGTX_FLASH.ld", cpu=("-mcpu=cortex-m4", "-mthumb", "-mfpu=fpv4-sp-d16", "-mfloat-abi=hard"),
                     defines=("-DDEBUG", "-DUSE_HAL_DRIVER", "-DSTM32F407xx")),
    "stm32h7": dict(mcu="STM32H753ZIT6", board="platforms/boards/nucleo_h753zi.repl",
                     core="Cortex-M7", clock=64, flash_kb=2048, ram_kb=1024,
                     project=ROOT / "firmware/stm32h7/mlkem_stm32h7_bench",
                     linker="STM32H753ZITX_FLASH.ld", cpu=("-mcpu=cortex-m7", "-mthumb", "-mfpu=fpv5-d16", "-mfloat-abi=hard"),
                     defines=("-DDEBUG", "-DUSE_HAL_DRIVER", "-DSTM32H753xx")),
}

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 16), b""):
            digest.update(block)
    return digest.hexdigest()

def command_version(command: list[str]) -> str:
    output = subprocess.run(command, capture_output=True, text=True, check=True).stdout
    return output.splitlines()[0]

def source_files(project: Path, variant: str) -> list[Path]:
    result: list[Path] = []
    selected = f"ml-kem-{variant}"
    for path in project.rglob("*"):
        if path.suffix not in (".c", ".s", ".S") or "Debug" in path.parts:
            continue
        if "mlkem" in path.parts and any(part.startswith("ml-kem-") and part != selected for part in path.parts):
            continue
        result.append(path)
    return sorted(result)

def include_dirs(project: Path, variant: str) -> list[str]:
    selected = f"ml-kem-{variant}"
    dirs = set()
    for path in project.rglob("*.h"):
        if "Debug" in path.parts:
            continue
        if "mlkem" in path.parts and any(part.startswith("ml-kem-") and part != selected for part in path.parts):
            continue
        dirs.add(str(path.parent))
    return [f"-I{item}" for item in sorted(dirs)]

def sections(elf: Path) -> dict[str, int]:
    result = subprocess.run(["arm-none-eabi-size", "-A", str(elf)], capture_output=True, text=True, check=True)
    values: dict[str, int] = {}
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1].isdigit():
            values[parts[0]] = int(parts[1])
    text, rodata, data, bss = (values.get(name, 0) for name in (".text", ".rodata", ".data", ".bss"))
    return {"text_bytes": text, "rodata_bytes": rodata, "data_bytes": data, "bss_bytes": bss,
            "flash_bytes": text + rodata + data, "static_ram_bytes": data + bss}

def build(target_name: str, target: dict, variant: str, opt: str, compiler_version: str, dry_run: bool) -> tuple[str, dict]:
    tag = opt[1:].lower()
    exp_id = f"{target_name}_mlkem{variant}_{target['clock']}mhz_{tag}"
    elf = BUILDS / f"{exp_id}.elf"
    map_file = BUILDS / f"{exp_id}.map"
    command = ["arm-none-eabi-gcc", "-std=gnu11", *target["cpu"], opt, "-ffunction-sections", "-fdata-sections",
               f"-DMLKEM_VARIANT_{variant}", f"-DMCU_CLOCK_MHZ={target['clock']}u", *target["defines"],
               *include_dirs(target["project"], variant), "-T", str(target["project"] / target["linker"]),
               *map(str, source_files(target["project"], variant)), "--specs=nosys.specs", "--specs=nano.specs",
               f"-Wl,-Map={map_file}", "-Wl,--gc-sections", "-o", str(elf), "-lm"]
    base = {"target": target_name, "mcu_model": target["mcu"], "board_model": target["board"], "core_arch": target["core"],
            "clock_mhz": target["clock"], "variant": f"ML-KEM-{variant}", "opt_level": opt, "elf_path": str(elf.resolve()),
            "map_path": str(map_file.resolve()), "compiler_version": compiler_version, "compiler_command": command,
            "built_at_utc": datetime.now(timezone.utc).isoformat()}
    if dry_run:
        return exp_id, {**base, "build_status": "DRY_RUN"}
    run = subprocess.run(command, capture_output=True, text=True)
    if run.returncode or not elf.exists():
        return exp_id, {**base, "build_status": "FAILED", "stderr": run.stderr[-4000:]}
    memory = sections(elf)
    status = "SUCCESS" if memory["static_ram_bytes"] <= target["ram_kb"] * 1024 else "STATIC_RAM_EXCEEDS_DEVICE"
    return exp_id, {**base, **memory, "elf_sha256": sha256(elf), "build_status": status}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--target", choices=TARGETS, action="append")
    args = parser.parse_args()
    if shutil.which("arm-none-eabi-gcc") is None or shutil.which("arm-none-eabi-size") is None:
        raise SystemExit("arm-none-eabi-gcc and arm-none-eabi-size must be on PATH.")
    BUILDS.mkdir(parents=True, exist_ok=True)
    compiler_version = command_version(["arm-none-eabi-gcc", "--version"])
    chosen = args.target or list(TARGETS)
    manifest = {"schema_version": 2, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "builds": {}}
    for target_name in chosen:
        for variant in VARIANTS:
            for opt in OPTS:
                exp_id, info = build(target_name, TARGETS[target_name], variant, opt, compiler_version, args.dry_run)
                manifest["builds"][exp_id] = info
                print(f"{info['build_status']:28} {exp_id}")
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    success = sum(info["build_status"] == "SUCCESS" for info in manifest["builds"].values())
    print(f"Built {success}/{len(manifest['builds'])} usable ELFs; manifest: {MANIFEST}")

if __name__ == "__main__":
    main()
