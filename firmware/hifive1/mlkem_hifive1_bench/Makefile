# Makefile for HiFive1 (RISC-V FE310 @ 320 MHz) ML-KEM Benchmark
# Toolchain: xPack RISC-V GCC (riscv-none-elf-gcc)

CC = "C:\Program Files\xpack-riscv-none-elf-gcc-15.2.0-1\bin\riscv-none-elf-gcc.exe"

ARCH_FLAGS = -march=rv32imac -mabi=ilp32 -mcmodel=medlow
CFLAGS     = $(ARCH_FLAGS) -O2 -std=gnu11 -Wall -ffunction-sections -fdata-sections

INCLUDES = -I. \
           -IInc \
           -Imlkem/common \
           -Imlkem/ml-kem-512 \
           -Imlkem/ml-kem-768 \
           -Imlkem/ml-kem-1024

SRCS = Src/main.c \
       Src/benchmark.c \
       mlkem/common/fips202.c \
       mlkem/common/randombytes.c \
       mlkem/ml-kem-512/cbd.c \
       mlkem/ml-kem-512/indcpa.c \
       mlkem/ml-kem-512/kem.c \
       mlkem/ml-kem-512/ntt.c \
       mlkem/ml-kem-512/poly.c \
       mlkem/ml-kem-512/polyvec.c \
       mlkem/ml-kem-512/reduce.c \
