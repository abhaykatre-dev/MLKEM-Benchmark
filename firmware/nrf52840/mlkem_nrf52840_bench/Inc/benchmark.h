/**
 * benchmark.h — nRF52840 Profile (ARM Cortex-M4 @ 64 MHz)
 * TIM2 Microsecond Hardware Precision Benchmark
 */

#ifndef INC_BENCHMARK_H_
#define INC_BENCHMARK_H_

#include <stdint.h>
#include "stm32f4xx_hal.h"

#define BENCHMARK_ITERATIONS  5
#ifndef MCU_CLOCK_MHZ
#define MCU_CLOCK_MHZ         64u    /* Cortex-M4 @ 64 MHz */
#endif

extern TIM_HandleTypeDef  htim2;
extern UART_HandleTypeDef huart2;

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
    uint8_t    decap_ok;
} BenchmarkResult;

void uart_print(const char *str);
void benchmark_mlkem512(BenchmarkResult *r);
void benchmark_mlkem768(BenchmarkResult *r);
void benchmark_mlkem1024(BenchmarkResult *r);
void benchmark_run_all(void);
void benchmark_print(BenchmarkResult *r);
void benchmark_print_csv_header(void);
void benchmark_print_csv_row(BenchmarkResult *r);

#endif /* INC_BENCHMARK_H_ */
