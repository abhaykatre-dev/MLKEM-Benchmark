/**
 * benchmark.h — SiFive HiFive1 Profile (16 KB SRAM, 48 MHz TIM2)
 *
 * ML-KEM Research Benchmark — NIST FIPS 203
 * SRAM: 16 KB (ML-KEM-512 supported; 768/1024 flagged OOM)
 */

#ifndef INC_BENCHMARK_H_
#define INC_BENCHMARK_H_

#include <stdint.h>
#include "stm32f0xx_hal.h"

#define BENCHMARK_ITERATIONS  1
#define MCU_CLOCK_MHZ         320u   /* RISC-V RV32IMAC @ 320 MHz */

typedef struct {
    uint32_t mean_us;
    uint32_t mean_cycles;
    uint32_t min_us;
    uint32_t max_us;
    uint32_t stddev_us;
} StatResult;

typedef struct {
    char       variant[16];
    StatResult keygen;
    StatResult encap;
    StatResult decap;
    uint8_t    decap_ok;   /* 1=PASS, 0=FAIL, 2=OOM(not run) */
} BenchmarkResult;

void uart_print(const char *str);
void benchmark_mlkem512(BenchmarkResult *r);
void benchmark_mlkem768_oom(BenchmarkResult *r);
void benchmark_mlkem1024_oom(BenchmarkResult *r);
void benchmark_run_all(void);
void benchmark_print(BenchmarkResult *r);
void benchmark_print_csv_header(void);
void benchmark_print_csv_row(BenchmarkResult *r);

#endif /* INC_BENCHMARK_H_ */
