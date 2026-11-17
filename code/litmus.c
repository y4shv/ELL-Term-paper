/*
 * Run the SB and MP litmus tests on x86-64.
 *
 * Two threads run on separate cores. Each iteration starts at a barrier,
 * runs the test, then meets again to record the result and reset x and y.
 *
 * Tests:
 *   sb          write x / read y, and write y / read x
 *   sb_mfence   same test with mfence between each write and read
 *   mp          write x then y; the other thread reads y then x
 *
 * Usage: ./litmus <test> <iterations> [skew]
 * skew delays thread 1 before its first instruction.
 */
#define _GNU_SOURCE
#include <pthread.h>
#include <sched.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Keep each shared variable on its own cache line. */
struct padded { _Atomic int v; char pad[60]; };
static struct padded X, Y, R1, BAR_COUNT, BAR_SENSE;

static long iterations;
static int skew;
enum { SB, SB_MFENCE, MP } test;

/* Relaxed atomics add no fence on x86-64. */
#define ST(var, val) atomic_store_explicit(&(var).v, (val), memory_order_relaxed)
#define LD(var)      atomic_load_explicit(&(var).v, memory_order_relaxed)
#define MFENCE()     __asm__ __volatile__("mfence" ::: "memory")

/* Two-thread sense-reversing barrier. */
static void barrier(int *local_sense)
{
    *local_sense = !*local_sense;
    if (atomic_fetch_add(&BAR_COUNT.v, 1) == 1) {
        atomic_store(&BAR_COUNT.v, 0);
        atomic_store(&BAR_SENSE.v, *local_sense);
    } else {
        while (atomic_load(&BAR_SENSE.v) != *local_sense)
            __builtin_ia32_pause();
    }
}

static void pin(int cpu)
{
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(cpu, &set);
    if (pthread_setaffinity_np(pthread_self(), sizeof set, &set) != 0) {
        fprintf(stderr, "could not pin to cpu %d\n", cpu);
        exit(1);
    }
}

static long counts[2][2];

/* Separate noinline functions make the test assembly easy to inspect. */
__attribute__((noinline)) int t0_sb(void)        { ST(X, 1); return LD(Y); }
__attribute__((noinline)) int t1_sb(void)        { ST(Y, 1); return LD(X); }
__attribute__((noinline)) int t0_sb_mfence(void) { ST(X, 1); MFENCE(); return LD(Y); }
__attribute__((noinline)) int t1_sb_mfence(void) { ST(Y, 1); MFENCE(); return LD(X); }
__attribute__((noinline)) void t0_mp(void)       { ST(X, 1); ST(Y, 1); }
__attribute__((noinline)) void t1_mp(int *r0, int *r1) { *r0 = LD(Y); *r1 = LD(X); }

static void *thread0(void *arg)
{
    (void)arg;
    pin(0);
    int sense = 0, r0 = 0;
    for (long i = 0; i < iterations; i++) {
        barrier(&sense);
        if (test == SB)             r0 = t0_sb();
        else if (test == SB_MFENCE) r0 = t0_sb_mfence();
        else                        t0_mp();
        barrier(&sense);
        if (test == MP) r0 = LD(R1) >> 1;          /* MP: T1 sends both regs */
        int r1 = (test == MP) ? (LD(R1) & 1) : LD(R1);
        counts[r0][r1]++;
        ST(X, 0);
        ST(Y, 0);
    }
    return NULL;
}

static void *thread1(void *arg)
{
    (void)arg;
    pin(1);
    int sense = 0;
    for (long i = 0; i < iterations; i++) {
        barrier(&sense);
        for (volatile int k = 0; k < skew; k++) { }
        if (test == SB)             ST(R1, t1_sb());
        else if (test == SB_MFENCE) ST(R1, t1_sb_mfence());
        else { int a, b; t1_mp(&a, &b); ST(R1, (a << 1) | b); }
        barrier(&sense);
    }
    return NULL;
}

int main(int argc, char **argv)
{
    if (argc < 3) {
        fprintf(stderr, "usage: %s sb|sb_mfence|mp iterations [skew]\n", argv[0]);
        return 1;
    }
    if (!strcmp(argv[1], "sb"))             test = SB;
    else if (!strcmp(argv[1], "sb_mfence")) test = SB_MFENCE;
    else if (!strcmp(argv[1], "mp"))        test = MP;
    else { fprintf(stderr, "unknown test %s\n", argv[1]); return 1; }
    iterations = atol(argv[2]);
    skew = argc > 3 ? atoi(argv[3]) : 0;

    pthread_t a, b;
    pthread_create(&a, NULL, thread0, NULL);
    pthread_create(&b, NULL, thread1, NULL);
    pthread_join(a, NULL);
    pthread_join(b, NULL);

    printf("test=%s iterations=%ld skew=%d  (0,0)=%ld (0,1)=%ld (1,0)=%ld (1,1)=%ld\n",
           argv[1], iterations, skew,
           counts[0][0], counts[0][1], counts[1][0], counts[1][1]);
    return 0;
}
