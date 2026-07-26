/**
 * benchmark.c — STM32F407VGT6 (ARM Cortex-M4 @ 168 MHz)
 * TIM2 Microsecond Hardware Precision Benchmark
 */

#include "benchmark.h"
#include <string.h>
#include <stdint.h>
#include <stdio.h>

#include "../mlkem/ml-kem-512/api.h"
#include "../mlkem/ml-kem-768/api.h"
#include "../mlkem/ml-kem-1024/api.h"

static uint8_t pk    [PQCLEAN_MLKEM1024_CLEAN_CRYPTO_PUBLICKEYBYTES];
static uint8_t sk    [PQCLEAN_MLKEM1024_CLEAN_CRYPTO_SECRETKEYBYTES];
static uint8_t ct    [PQCLEAN_MLKEM1024_CLEAN_CRYPTO_CIPHERTEXTBYTES];
static uint8_t ss_enc[PQCLEAN_MLKEM1024_CLEAN_CRYPTO_BYTES];
static uint8_t ss_dec[PQCLEAN_MLKEM1024_CLEAN_CRYPTO_BYTES];

static uint32_t kg_times [BENCHMARK_ITERATIONS];
static uint32_t enc_times[BENCHMARK_ITERATIONS];
static uint32_t dec_times[BENCHMARK_ITERATIONS];

extern TIM_HandleTypeDef  htim2;
extern UART_HandleTypeDef huart2;

void uart_print(const char *str)
{
    HAL_UART_Transmit(&huart2, (uint8_t *)str, (uint16_t)strlen(str), HAL_MAX_DELAY);
}

static uint32_t isqrt32(uint64_t val)
{
    if (val == 0) return 0;
    uint64_t x = val, y = 1;
    while (x > y) { x = (x + y) / 2; y = val / x; }
    return (uint32_t)x;
}

static void compute_stats(uint32_t *times, uint32_t count, StatResult *res)
{
    uint32_t i;
    uint64_t sum  = 0;
    uint32_t minv = UINT32_MAX, maxv = 0;

    for (i = 0; i < count; i++) {
        sum += times[i];
        if (times[i] < minv) minv = times[i];
        if (times[i] > maxv) maxv = times[i];
    }

    res->mean_us     = (uint32_t)(sum / count);
    res->mean_cycles = res->mean_us * MCU_CLOCK_MHZ;
    res->min_us      = minv;
    res->max_us      = maxv;

    uint64_t var = 0;
    uint32_t m = res->mean_us;
    for (i = 0; i < count; i++) {
        int64_t d = (int64_t)times[i] - (int64_t)m;
        var += (uint64_t)(d * d);
    }
    res->stddev_us = isqrt32(var / count);
}

void benchmark_mlkem512(BenchmarkResult *r)
{
    uint32_t i, t_start, t_end;
    uint8_t all_pass = 1;
    memset(r, 0, sizeof(BenchmarkResult));
    strncpy(r->variant, "ML-KEM-512", sizeof(r->variant) - 1);

    for (i = 0; i < BENCHMARK_ITERATIONS; i++) {
        __disable_irq();
        __HAL_TIM_SET_COUNTER(&htim2, 0);
        t_start = __HAL_TIM_GET_COUNTER(&htim2);
        PQCLEAN_MLKEM512_CLEAN_crypto_kem_keypair(pk, sk);
        t_end = __HAL_TIM_GET_COUNTER(&htim2);
        __enable_irq();
        kg_times[i] = t_end - t_start;

        __disable_irq();
        __HAL_TIM_SET_COUNTER(&htim2, 0);
        t_start = __HAL_TIM_GET_COUNTER(&htim2);
        PQCLEAN_MLKEM512_CLEAN_crypto_kem_enc(ct, ss_enc, pk);
        t_end = __HAL_TIM_GET_COUNTER(&htim2);
        __enable_irq();
        enc_times[i] = t_end - t_start;

        __disable_irq();
        __HAL_TIM_SET_COUNTER(&htim2, 0);
        t_start = __HAL_TIM_GET_COUNTER(&htim2);
        PQCLEAN_MLKEM512_CLEAN_crypto_kem_dec(ss_dec, ct, sk);
        t_end = __HAL_TIM_GET_COUNTER(&htim2);
        __enable_irq();
        dec_times[i] = t_end - t_start;

        if (memcmp(ss_enc, ss_dec, PQCLEAN_MLKEM512_CLEAN_CRYPTO_BYTES) != 0)
            all_pass = 0;
    }
    r->decap_ok = all_pass;
    compute_stats(kg_times,  BENCHMARK_ITERATIONS, &r->keygen);
    compute_stats(enc_times, BENCHMARK_ITERATIONS, &r->encap);
    compute_stats(dec_times, BENCHMARK_ITERATIONS, &r->decap);
}

void benchmark_mlkem768(BenchmarkResult *r)
{
    uint32_t i, t_start, t_end;
    uint8_t all_pass = 1;
    memset(r, 0, sizeof(BenchmarkResult));
    strncpy(r->variant, "ML-KEM-768", sizeof(r->variant) - 1);

    for (i = 0; i < BENCHMARK_ITERATIONS; i++) {
        __disable_irq();
        __HAL_TIM_SET_COUNTER(&htim2, 0);
        t_start = __HAL_TIM_GET_COUNTER(&htim2);
        PQCLEAN_MLKEM768_CLEAN_crypto_kem_keypair(pk, sk);
        t_end = __HAL_TIM_GET_COUNTER(&htim2);
        __enable_irq();
        kg_times[i] = t_end - t_start;

        __disable_irq();
        __HAL_TIM_SET_COUNTER(&htim2, 0);
        t_start = __HAL_TIM_GET_COUNTER(&htim2);
        PQCLEAN_MLKEM768_CLEAN_crypto_kem_enc(ct, ss_enc, pk);
        t_end = __HAL_TIM_GET_COUNTER(&htim2);
        __enable_irq();
        enc_times[i] = t_end - t_start;

        __disable_irq();
        __HAL_TIM_SET_COUNTER(&htim2, 0);
        t_start = __HAL_TIM_GET_COUNTER(&htim2);
        PQCLEAN_MLKEM768_CLEAN_crypto_kem_dec(ss_dec, ct, sk);
        t_end = __HAL_TIM_GET_COUNTER(&htim2);
        __enable_irq();
        dec_times[i] = t_end - t_start;

        if (memcmp(ss_enc, ss_dec, PQCLEAN_MLKEM768_CLEAN_CRYPTO_BYTES) != 0)
            all_pass = 0;
    }
    r->decap_ok = all_pass;
    compute_stats(kg_times,  BENCHMARK_ITERATIONS, &r->keygen);
    compute_stats(enc_times, BENCHMARK_ITERATIONS, &r->encap);
    compute_stats(dec_times, BENCHMARK_ITERATIONS, &r->decap);
}

void benchmark_mlkem1024(BenchmarkResult *r)
{
    uint32_t i, t_start, t_end;
    uint8_t all_pass = 1;
    memset(r, 0, sizeof(BenchmarkResult));
    strncpy(r->variant, "ML-KEM-1024", sizeof(r->variant) - 1);

    for (i = 0; i < BENCHMARK_ITERATIONS; i++) {
        __disable_irq();
        __HAL_TIM_SET_COUNTER(&htim2, 0);
        t_start = __HAL_TIM_GET_COUNTER(&htim2);
        PQCLEAN_MLKEM1024_CLEAN_crypto_kem_keypair(pk, sk);
        t_end = __HAL_TIM_GET_COUNTER(&htim2);
        __enable_irq();
        kg_times[i] = t_end - t_start;

        __disable_irq();
        __HAL_TIM_SET_COUNTER(&htim2, 0);
        t_start = __HAL_TIM_GET_COUNTER(&htim2);
        PQCLEAN_MLKEM1024_CLEAN_crypto_kem_enc(ct, ss_enc, pk);
        t_end = __HAL_TIM_GET_COUNTER(&htim2);
        __enable_irq();
        enc_times[i] = t_end - t_start;

        __disable_irq();
        __HAL_TIM_SET_COUNTER(&htim2, 0);
        t_start = __HAL_TIM_GET_COUNTER(&htim2);
        PQCLEAN_MLKEM1024_CLEAN_crypto_kem_dec(ss_dec, ct, sk);
        t_end = __HAL_TIM_GET_COUNTER(&htim2);
        __enable_irq();
        dec_times[i] = t_end - t_start;

        if (memcmp(ss_enc, ss_dec, PQCLEAN_MLKEM1024_CLEAN_CRYPTO_BYTES) != 0)
            all_pass = 0;
    }
    r->decap_ok = all_pass;
    compute_stats(kg_times,  BENCHMARK_ITERATIONS, &r->keygen);
    compute_stats(enc_times, BENCHMARK_ITERATIONS, &r->encap);
    compute_stats(dec_times, BENCHMARK_ITERATIONS, &r->decap);
}

void benchmark_run_all(void)
{
    BenchmarkResult r512, r768, r1024;

    uart_print("\r\n=======================================================\r\n");
    uart_print("  RESEARCH-GRADE ML-KEM BENCHMARK (NIST FIPS 203)\r\n");
    uart_print("  Target Processor: STM32F407VGT6 (ARM Cortex-M4F)\r\n");
    uart_print("  Clock Speed:      168 MHz | TIM2 Prescaler 1us/tick\r\n");
    uart_print("  Memory Specs:     1024 KB Flash | 192 KB SRAM\r\n");
    uart_print("  Sampling Count:   N = 5 Iterations (Interrupt Isolated)\r\n");
    uart_print("=======================================================\r\n");

    uart_print("\r\nExecuting ML-KEM-512 Benchmark (5 runs)...\r\n");
    benchmark_mlkem512(&r512);
    benchmark_print(&r512);

    uart_print("\r\nExecuting ML-KEM-768 Benchmark (5 runs)...\r\n");
    benchmark_mlkem768(&r768);
    benchmark_print(&r768);

    uart_print("\r\nExecuting ML-KEM-1024 Benchmark (5 runs)...\r\n");
    benchmark_mlkem1024(&r1024);
    benchmark_print(&r1024);

    benchmark_print_csv_header();
    benchmark_print_csv_row(&r512);
    benchmark_print_csv_row(&r768);
    benchmark_print_csv_row(&r1024);

    uart_print("\r\n=======================================================\r\n");
    uart_print("  STM32F4 BENCHMARK SUITE COMPLETE!\r\n");
    uart_print("=======================================================\r\n");
}

void benchmark_print(BenchmarkResult *r)
{
    char buf[220];
    uart_print("\r\n");
    snprintf(buf, sizeof(buf), "[ VARIANT: %s ]\r\n", r->variant);
    uart_print(buf);
    snprintf(buf, sizeof(buf),
        "  KeyGen : %8lu us | %10lu cycles | Min %5lu | Max %5lu | StdDev %lu us\r\n",
        r->keygen.mean_us, r->keygen.mean_cycles,
        r->keygen.min_us, r->keygen.max_us, r->keygen.stddev_us);
    uart_print(buf);
    snprintf(buf, sizeof(buf),
        "  Encap  : %8lu us | %10lu cycles | Min %5lu | Max %5lu | StdDev %lu us\r\n",
        r->encap.mean_us, r->encap.mean_cycles,
        r->encap.min_us, r->encap.max_us, r->encap.stddev_us);
    uart_print(buf);
    snprintf(buf, sizeof(buf),
        "  Decap  : %8lu us | %10lu cycles | Min %5lu | Max %5lu | StdDev %lu us\r\n",
        r->decap.mean_us, r->decap.mean_cycles,
        r->decap.min_us, r->decap.max_us, r->decap.stddev_us);
    uart_print(buf);
    snprintf(buf, sizeof(buf), "  Status : %s\r\n",
        r->decap_ok ? "PASS [Shared Secret Match]" : "FAIL [Mismatch]");
    uart_print(buf);
}

void benchmark_print_csv_header(void)
{
    uart_print("\r\n--- CSV DATASET OUTPUT ---\r\n");
    uart_print("variant,keygen_cycles,encap_cycles,decap_cycles,"
               "keygen_us,encap_us,decap_us,keygen_stddev,encap_stddev,decap_stddev,decap_ok\r\n");
}

void benchmark_print_csv_row(BenchmarkResult *r)
{
    char buf[240];
    snprintf(buf, sizeof(buf),
        "%s,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%u\r\n",
        r->variant,
        r->keygen.mean_cycles, r->encap.mean_cycles, r->decap.mean_cycles,
        r->keygen.mean_us,     r->encap.mean_us,     r->decap.mean_us,
        r->keygen.stddev_us,   r->encap.stddev_us,   r->decap.stddev_us,
        r->decap_ok);
    uart_print(buf);
}
