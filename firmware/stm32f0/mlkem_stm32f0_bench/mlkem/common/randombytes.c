/**
 * randombytes_stub.c
 *
 * Bare-metal random bytes provider for STM32F4.
 * For benchmarking purposes only — uses a deterministic seed.
 * NOT suitable for production cryptography.
 *
 * In a real deployment, replace this with hardware RNG (STM32F4 has TRNG on some variants)
 * or a DRBG seeded from hardware entropy.
 */

#include <stdint.h>
#include "randombytes.h"

/* Simple xorshift32 PRNG — deterministic, sufficient for benchmark reproducibility */
static uint32_t rng_state = 0xDEADBEEF;

static uint32_t xorshift32(void)
{
    rng_state ^= rng_state << 13;
    rng_state ^= rng_state >> 17;
    rng_state ^= rng_state << 5;
    return rng_state;
}

void randombytes(uint8_t *out, size_t outlen)
{
    size_t i = 0;
    uint32_t val;

    for (i = 0; i + 4 <= outlen; i += 4) {
        val = xorshift32();
        out[i + 0] = (uint8_t)(val >> 0);
        out[i + 1] = (uint8_t)(val >> 8);
        out[i + 2] = (uint8_t)(val >> 16);
        out[i + 3] = (uint8_t)(val >> 24);
    }
    /* Handle remaining bytes */
    if (i < outlen) {
        val = xorshift32();
        for (; i < outlen; i++) {
            out[i] = (uint8_t)(val & 0xFF);
            val >>= 8;
        }
    }
}
