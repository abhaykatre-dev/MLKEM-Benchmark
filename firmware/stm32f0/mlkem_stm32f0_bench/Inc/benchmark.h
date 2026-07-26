/**
 * benchmark.h
 *
 * ML-KEM Benchmark Driver for STM32F0 (Cortex-M0 @ 48 MHz)
 * Statistical Benchmarking (N=100) using TIM2 Microsecond Timer.
 *
 * Project: Benchmarking ML-KEM on IoT Processors
 * Target:  STM32F072RBT6 @ 48 MHz (Cortex-M0)
 */

#ifndef BENCHMARK_H
#define BENCHMARK_H

#include <stdint.h>
#include "stm32f0xx_hal.h"

#define BENCHMARK_ITERATIONS 1

/* ── External handles from main.c ── */
extern TIM_HandleTypeDef htim2;
extern UART_HandleTypeDef huart2;

/* ── Operation statistical summary ── */
typedef struct {
    uint32_t min_us;
    uint32_t max_us;
    uint32_t mean_us;
    uint32_t mean_cycles;
    uint32_t stddev_us;
} StatResult;

/* ── Variant benchmark summary ── */
typedef struct {
    char       variant[16];
    StatResult keygen;
    StatResult encap;
    StatResult decap;
    uint8_t    decap_ok; /* 1 = PASS, 0 = FAIL */
} BenchmarkResult;

/* ── Timing macro for TIM2 (1us resolution) ── */
#define TIM2_US()       (__HAL_TIM_GET_COUNTER(&htim2))

/* ── Function declarations ── */
void benchmark_mlkem512(BenchmarkResult *r);
void benchmark_mlkem768(BenchmarkResult *r);
void benchmark_mlkem1024(BenchmarkResult *r);
void benchmark_run_all(void);
void benchmark_print(BenchmarkResult *r);
void benchmark_print_csv_header(void);
void benchmark_print_csv_row(BenchmarkResult *r);
void uart_print(const char *str);

#endif /* BENCHMARK_H */
