#ifndef RANDOMBYTES_H
#define RANDOMBYTES_H

#include <stdint.h>
#include <stddef.h>

/**
 * Fill `outlen` bytes at `out` with (pseudo)random data.
 * Benchmark stub — deterministic xorshift32 PRNG.
 */
void randombytes(uint8_t *out, size_t outlen);

#endif /* RANDOMBYTES_H */
