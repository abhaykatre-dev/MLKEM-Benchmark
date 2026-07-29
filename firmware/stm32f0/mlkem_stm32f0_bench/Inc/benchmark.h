/**
 * benchmark.h — STM32F072RBT6 (ARM Cortex-M0 @ 48 MHz)
 * TIM2 Microsecond Precision Timing & Stack Watermarking
 */

#ifndef BENCHMARK_H
#define BENCHMARK_H

#include <stdint.h>
#include "stm32f0xx_hal.h"

#ifndef BENCHMARK_ITERATIONS
#define BENCHMARK_ITERATIONS  5
#endif

#ifndef MCU_CLOCK_MHZ
#define MCU_CLOCK_MHZ         48u
#endif

/* Default to ML-KEM-512 if not specified */
#if !defined(MLKEM_VARIANT_512) && !defined(MLKEM_VARIANT_768) && !defined(MLKEM_VARIANT_1024)
#define MLKEM_VARIANT_512
#endif

#if defined(MLKEM_VARIANT_512)
#define MLKEM_VARIANT_NAME "ML-KEM-512"
#include "../mlkem/ml-kem-512/api.h"
#define CRYPTO_PUBLICKEYBYTES  PQCLEAN_MLKEM512_CLEAN_CRYPTO_PUBLICKEYBYTES
#define CRYPTO_SECRETKEYBYTES  PQCLEAN_MLKEM512_CLEAN_CRYPTO_SECRETKEYBYTES
#define CRYPTO_CIPHERTEXTBYTES PQCLEAN_MLKEM512_CLEAN_CRYPTO_CIPHERTEXTBYTES
#define CRYPTO_BYTES           PQCLEAN_MLKEM512_CLEAN_CRYPTO_BYTES
#define crypto_kem_keypair     PQCLEAN_MLKEM512_CLEAN_crypto_kem_keypair
#define crypto_kem_enc         PQCLEAN_MLKEM512_CLEAN_crypto_kem_enc
#define crypto_kem_dec         PQCLEAN_MLKEM512_CLEAN_crypto_kem_dec
#elif defined(MLKEM_VARIANT_768)
#define MLKEM_VARIANT_NAME "ML-KEM-768"
#include "../mlkem/ml-kem-768/api.h"
#define CRYPTO_PUBLICKEYBYTES  PQCLEAN_MLKEM768_CLEAN_CRYPTO_PUBLICKEYBYTES
#define CRYPTO_SECRETKEYBYTES  PQCLEAN_MLKEM768_CLEAN_CRYPTO_SECRETKEYBYTES
#define CRYPTO_CIPHERTEXTBYTES PQCLEAN_MLKEM768_CLEAN_CRYPTO_CIPHERTEXTBYTES
#define CRYPTO_BYTES           PQCLEAN_MLKEM768_CLEAN_CRYPTO_BYTES
#define crypto_kem_keypair     PQCLEAN_MLKEM768_CLEAN_crypto_kem_keypair
#define crypto_kem_enc         PQCLEAN_MLKEM768_CLEAN_crypto_kem_enc
#define crypto_kem_dec         PQCLEAN_MLKEM768_CLEAN_crypto_kem_dec
#elif defined(MLKEM_VARIANT_1024)
#define MLKEM_VARIANT_NAME "ML-KEM-1024"
#include "../mlkem/ml-kem-1024/api.h"
#define CRYPTO_PUBLICKEYBYTES  PQCLEAN_MLKEM1024_CLEAN_CRYPTO_PUBLICKEYBYTES
#define CRYPTO_SECRETKEYBYTES  PQCLEAN_MLKEM1024_CLEAN_CRYPTO_SECRETKEYBYTES
#define CRYPTO_CIPHERTEXTBYTES PQCLEAN_MLKEM1024_CLEAN_CRYPTO_CIPHERTEXTBYTES
#define CRYPTO_BYTES           PQCLEAN_MLKEM1024_CLEAN_CRYPTO_BYTES
#define crypto_kem_keypair     PQCLEAN_MLKEM1024_CLEAN_crypto_kem_keypair
#define crypto_kem_enc         PQCLEAN_MLKEM1024_CLEAN_crypto_kem_enc
#define crypto_kem_dec         PQCLEAN_MLKEM1024_CLEAN_crypto_kem_dec
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
    uint32_t   peak_stack_bytes;
    uint8_t    decap_ok;
} BenchmarkResult;

void uart_print(const char *str);
void stack_paint(void);
uint32_t stack_watermark_get(void);
void benchmark_run(BenchmarkResult *r);
void benchmark_print_results(BenchmarkResult *r);

#endif /* BENCHMARK_H */
