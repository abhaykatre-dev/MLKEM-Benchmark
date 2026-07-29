/**
 * benchmark.c — STM32F407VGT6 (ARM Cortex-M4 @ 168 MHz)
 * TIM2 Microsecond Hardware Precision Benchmark & Stack Watermarking
 */

#include "benchmark.h"
#include <string.h>
#include <stdint.h>
#include <stdio.h>

#define STACK_FILL_PATTERN 0x5A5A5A5A

extern uint32_t _ebss;
extern uint32_t _estack;

static uint8_t pk    [CRYPTO_PUBLICKEYBYTES];
static uint8_t sk    [CRYPTO_SECRETKEYBYTES];
static uint8_t ct    [CRYPTO_CIPHERTEXTBYTES];
static uint8_t ss_enc[CRYPTO_BYTES];
static uint8_t ss_dec[CRYPTO_BYTES];

static uint32_t kg_times [BENCHMARK_ITERATIONS];
static uint32_t enc_times[BENCHMARK_ITERATIONS];
static uint32_t dec_times[BENCHMARK_ITERATIONS];

void uart_print(const char *str)
{
    HAL_UART_Transmit(&huart2, (uint8_t *)str, (uint16_t)strlen(str), HAL_MAX_DELAY);
}

void stack_paint(void)
{
    register uint32_t *p = (uint32_t*)&_ebss + 64;
    register uint32_t *sp;
    __asm__ volatile ("mov %0, sp" : "=r"(sp));
    
    while (p < (sp - 64)) {
        *p++ = STACK_FILL_PATTERN;
    }
}

uint32_t stack_watermark_get(void)
{
    register uint32_t *p = (uint32_t*)&_estack - 16;
    register uint32_t *bot = (uint32_t*)&_ebss + 64;

    while (p > bot && *p != STACK_FILL_PATTERN) {
        p--;
    }

    uint32_t lowest_sp = (uint32_t)p;
    uint32_t top_addr  = (uint32_t)&_estack;
    return (top_addr > lowest_sp) ? (top_addr - lowest_sp) : 0;
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
        int32_t diff = (int32_t)times[i] - (int32_t)m;
        var += (uint64_t)(diff * diff);
    }
    res->stddev_us = isqrt32(var / count);
}

void benchmark_run(BenchmarkResult *r)
{
    uint32_t i;
    memset(r, 0, sizeof(BenchmarkResult));
    strncpy(r->variant, MLKEM_VARIANT_NAME, sizeof(r->variant) - 1);

    HAL_TIM_Base_Start(&htim2);
    stack_paint();

    for (i = 0; i < BENCHMARK_ITERATIONS; i++) {
        __HAL_TIM_SET_COUNTER(&htim2, 0);
        int res_kg = crypto_kem_keypair(pk, sk);
        kg_times[i] = __HAL_TIM_GET_COUNTER(&htim2);
        if (res_kg != 0) { r->decap_ok = 0; return; }

        __HAL_TIM_SET_COUNTER(&htim2, 0);
        int res_enc = crypto_kem_enc(ct, ss_enc, pk);
        enc_times[i] = __HAL_TIM_GET_COUNTER(&htim2);
        if (res_enc != 0) { r->decap_ok = 0; return; }

        __HAL_TIM_SET_COUNTER(&htim2, 0);
        int res_dec = crypto_kem_dec(ss_dec, ct, sk);
        dec_times[i] = __HAL_TIM_GET_COUNTER(&htim2);
        if (res_dec != 0) { r->decap_ok = 0; return; }
    }

    compute_stats(kg_times,  BENCHMARK_ITERATIONS, &r->keygen);
    compute_stats(enc_times, BENCHMARK_ITERATIONS, &r->encap);
    compute_stats(dec_times, BENCHMARK_ITERATIONS, &r->decap);

    r->peak_stack_bytes = stack_watermark_get();
    r->decap_ok = (memcmp(ss_enc, ss_dec, CRYPTO_BYTES) == 0) ? 1 : 0;
}

void benchmark_print_results(BenchmarkResult *r)
{
    char buf[256];

    snprintf(buf, sizeof(buf), "\r\n=======================================================\r\n");
    uart_print(buf);
    snprintf(buf, sizeof(buf), "  RESEARCH-GRADE ML-KEM BENCHMARK (NIST FIPS 203)\r\n");
    uart_print(buf);
    snprintf(buf, sizeof(buf), "  Target Processor: STM32F407VGT6 (ARM Cortex-M4F)\r\n");
    uart_print(buf);
    snprintf(buf, sizeof(buf), "  Variant Compiled: %s\r\n", r->variant);
    uart_print(buf);
    snprintf(buf, sizeof(buf), "=======================================================\r\n\r\n");
    uart_print(buf);

    if (r->decap_ok) {
        snprintf(buf, sizeof(buf), "--- CSV DATASET OUTPUT ---\r\n");
        uart_print(buf);
        snprintf(buf, sizeof(buf), "variant,keygen_cycles,encap_cycles,decap_cycles,keygen_us,encap_us,decap_us,keygen_stddev,encap_stddev,decap_stddev,decap_ok,peak_stack\r\n");
        uart_print(buf);
        snprintf(buf, sizeof(buf), "%s,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%u,%lu\r\n",
                 r->variant,
                 r->keygen.mean_cycles, r->encap.mean_cycles, r->decap.mean_cycles,
                 r->keygen.mean_us,     r->encap.mean_us,     r->decap.mean_us,
                 r->keygen.stddev_us,   r->encap.stddev_us,   r->decap.stddev_us,
                 r->decap_ok, r->peak_stack_bytes);
        uart_print(buf);
    } else {
        snprintf(buf, sizeof(buf), "--- CSV DATASET OUTPUT ---\r\n");
        uart_print(buf);
        snprintf(buf, sizeof(buf), "variant,keygen_cycles,encap_cycles,decap_cycles,keygen_us,encap_us,decap_us,keygen_stddev,encap_stddev,decap_stddev,decap_ok,peak_stack\r\n");
        uart_print(buf);
        snprintf(buf, sizeof(buf), "%s,FAIL,FAIL,FAIL,FAIL,FAIL,FAIL,0,0,0,0,0\r\n", r->variant);
        uart_print(buf);
    }

    snprintf(buf, sizeof(buf), "\r\nBENCHMARK SUITE COMPLETE!\r\n");
    uart_print(buf);
}
