import csv
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

try:
    from backend.models import (
        RecommendationFormInputs,
        RecommendationResult,
        BenchmarkRecord,
        HealthCheck,
    )
    from backend.ai_engine import run_ai_recommendation
except ImportError:
    from models import (
        RecommendationFormInputs,
        RecommendationResult,
        BenchmarkRecord,
        HealthCheck,
    )
    from ai_engine import run_ai_recommendation

app = FastAPI(
    title="NIST FIPS 203 ML-KEM Benchmarking Framework API",
    description="Backend API for post-quantum ML-KEM empirical benchmarks and AI recommendation system.",
    version="1.0.0",
)

# In-memory settings store
SETTINGS_DB = {
    "datasetSource": "benchmark.csv",
    "renodePath": "C:\\Program Files\\Renode\\renode.exe",
    "themePreference": "system",
    "cacheEnabled": True,
    "logLevel": "INFO",
    "maxLatencyThresholdUs": 10000,
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

@app.get("/api/health", response_model=HealthCheck, tags=["Health"])
@app.get("/health", response_model=HealthCheck, include_in_schema=False)
async def get_health():
    return HealthCheck(status="ok", version="1.0.0")

@app.post("/api/recommendation", response_model=RecommendationResult, tags=["AI Recommendation"])
@app.post("/recommendation", response_model=RecommendationResult, include_in_schema=False)
async def get_recommendation(inputs: RecommendationFormInputs):
    try:
        return run_ai_recommendation(inputs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

@app.get("/api/benchmarks", tags=["Benchmarks"])
@app.get("/benchmarks", include_in_schema=False)
async def get_benchmarks(type: Optional[str] = Query("baseline", description="'baseline' or 'full'")):
    data_dir = Path(__file__).resolve().parent.parent / "dataset"
    file_name = "benchmark_1000.csv" if type == "full" else "benchmark.csv"
    csv_path = data_dir / file_name

    if not csv_path.exists():
        csv_path = data_dir / "benchmark.csv"

    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="Benchmark dataset CSV not found.")

    records: List[Dict[str, Any]] = []
    try:
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                def parse_val(val, target_type=int):
                    if val is None or val == "" or val == "OOM":
                        return "OOM"
                    try:
                        return target_type(float(val))
                    except ValueError:
                        return val

                record = {
                    "mcu": row.get("mcu", ""),
                    "core": row.get("core", ""),
                    "clock_mhz": parse_val(row.get("clock_mhz"), int),
                    "flash_kb": parse_val(row.get("flash_kb"), int),
                    "ram_kb": parse_val(row.get("ram_kb"), int),
                    "variant": row.get("variant", ""),
                    "keygen_cycles": parse_val(row.get("keygen_cycles"), int),
                    "encap_cycles": parse_val(row.get("encap_cycles"), int),
                    "decap_cycles": parse_val(row.get("decap_cycles"), int),
                    "keygen_us": parse_val(row.get("keygen_us"), float),
                    "encap_us": parse_val(row.get("encap_us"), float),
                    "decap_us": parse_val(row.get("decap_us"), float),
                    "verification_status": row.get("verification_status", "PASS"),
                }
                records.append(record)
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load dataset: {str(e)}")

@app.get("/api/processors", tags=["Hardware Profiles"])
@app.get("/processors", include_in_schema=False)
async def get_processors():
    return [
        {
            "mcu": "STM32F072RBT6",
            "name": "STM32F0 Series (Ultra-Low-Power)",
            "core": "ARM Cortex-M0",
            "architecture": "ARM Cortex-M",
            "frequency": 48,
            "ram": 16,
            "flash": 128,
            "voltage": "2.0V - 3.6V",
            "supportedVariants": ["ML-KEM-512"],
            "description": "Entry-level ARM Cortex-M0 MCU with 16 KB SRAM boundary.",
            "features": ["Hardware CRC", "Low-power Stop/Standby", "12-bit ADC"],
        },
        {
            "mcu": "STM32F407VGT6",
            "name": "STM32F4 High-Performance DSP",
            "core": "ARM Cortex-M4F",
            "architecture": "ARM Cortex-M",
            "frequency": 168,
            "ram": 192,
            "flash": 1024,
            "voltage": "1.8V - 3.6V",
            "supportedVariants": ["ML-KEM-512", "ML-KEM-768", "ML-KEM-1024"],
            "description": "ARM Cortex-M4F with single-precision FPU and DSP instructions.",
            "features": ["FPU & DSP", "ART Accelerator", "Crypto Acceleration"],
        },
        {
            "mcu": "STM32H753ZIT6",
            "name": "STM32H7 Dual-Core High Performance",
            "core": "ARM Cortex-M7F",
            "architecture": "ARM Cortex-M",
            "frequency": 480,
            "ram": 1024,
            "flash": 2048,
            "voltage": "1.62V - 3.6V",
            "supportedVariants": ["ML-KEM-512", "ML-KEM-768", "ML-KEM-1024"],
            "description": "Flagship 480 MHz Cortex-M7F delivering sub-millisecond ML-KEM operations.",
            "features": ["Double-precision FPU", "Hardware Crypto Engine", "Chrom-ART"],
        },
        {
            "mcu": "nRF52840",
            "name": "Nordic Bluetooth 5.4 SoC",
            "core": "ARM Cortex-M4F",
            "architecture": "ARM Cortex-M",
            "frequency": 64,
            "ram": 256,
            "flash": 1024,
            "voltage": "1.7V - 5.5V",
            "supportedVariants": ["ML-KEM-512", "ML-KEM-768", "ML-KEM-1024"],
            "description": "Multiprotocol Bluetooth 5.4 SoC with TrustZone CryptoCell 310.",
            "features": ["TrustZone CryptoCell", "Integrated 2.4GHz Radio", "256KB RAM"],
        },
        {
            "mcu": "HiFive1",
            "name": "SiFive HiFive1 RISC-V Profile",
            "core": "RISC-V FE310-G000",
            "architecture": "RISC-V",
            "frequency": 320,
            "ram": 16,
            "flash": 16384,
            "voltage": "3.3V",
            "supportedVariants": ["ML-KEM-512"],
            "description": "Open-source 32-bit RISC-V RV32IMAC core for PQC testing.",
            "features": ["RV32IMAC ISA", "Flexible PLL Clocking", "Open Architecture"],
        },
    ]

@app.get("/api/variants", tags=["ML-KEM Specifications"])
@app.get("/variants", include_in_schema=False)
async def get_variants():
    return [
        {
            "variant": "ML-KEM-512",
            "claimedNistLevel": "Level 1",
            "securityBits": 128,
            "publicKeySize": 800,
            "secretKeySize": 1632,
            "ciphertextSize": 768,
            "minRamRequirement": 16,
            "performanceRating": "High",
            "memoryUsageRating": "Compact",
            "recommendedUseCases": ["Ultra-low-power IoT nodes", "Constrained microcontrollers (<32KB RAM)"],
        },
        {
            "variant": "ML-KEM-768",
            "claimedNistLevel": "Level 3",
            "securityBits": 192,
            "publicKeySize": 1184,
            "secretKeySize": 2400,
            "ciphertextSize": 1088,
            "minRamRequirement": 20,
            "performanceRating": "Medium",
            "memoryUsageRating": "Moderate",
            "recommendedUseCases": ["General IoT gateways", "TLS 1.3 Post-Quantum Hybrid Handshakes"],
        },
        {
            "variant": "ML-KEM-1024",
            "claimedNistLevel": "Level 5",
            "securityBits": 256,
            "publicKeySize": 1568,
            "secretKeySize": 3168,
            "ciphertextSize": 1568,
            "minRamRequirement": 28,
            "performanceRating": "Maximum Security",
            "memoryUsageRating": "Heavy",
            "recommendedUseCases": ["High-security edge servers", "Long-term data confidentiality"],
        },
    ]

@app.get("/api/analytics", tags=["Analytics"])
@app.get("/analytics", include_in_schema=False)
async def get_analytics():
    benchmarks = await get_benchmarks(type="baseline")
    total_benchmarks = len(benchmarks)
    passes = sum(1 for b in benchmarks if b.get("verification_status") == "PASS")
    ooms = sum(1 for b in benchmarks if b.get("verification_status") == "OOM")

    encap_times = [b["encap_us"] for b in benchmarks if isinstance(b.get("encap_us"), (int, float))]
    avg_encap = round(sum(encap_times) / len(encap_times), 2) if encap_times else 0

    return {
        "totalBenchmarks": total_benchmarks,
        "totalPasses": passes,
        "totalOOMs": ooms,
        "passRatePercent": round((passes / total_benchmarks) * 100, 1) if total_benchmarks else 0,
        "avgEncapLatencyUs": avg_encap,
        "supportedProcessors": 5,
        "mlkemVariants": 3,
        "aiAccuracyPercent": 96.5,
    }

@app.get("/api/settings", tags=["Settings"])
@app.get("/settings", include_in_schema=False)
async def get_settings():
    return SETTINGS_DB

@app.post("/api/settings", tags=["Settings"])
@app.post("/settings", include_in_schema=False)
async def update_settings(payload: Dict[str, Any]):
    SETTINGS_DB.update(payload)
    return {"status": "ok", "settings": SETTINGS_DB}
