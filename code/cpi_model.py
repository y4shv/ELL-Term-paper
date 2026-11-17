#!/usr/bin/env python3
"""A small CPI model comparing stalls with a store buffer (Chapter 8).

Prints the simple CPI formula and a cycle-by-cycle simulation as buffer size
changes. This is a model, not a measurement of a real processor.
"""
import random

N = 200_000  # instructions per run
SEED = 305


def stall_cpi(f, latencies):
    return 1 + f * sum(latencies) / len(latencies)


def simulate(f, m, l_hit, l_miss, B, seed=SEED):
    """Cycles per instruction of the buffered design."""
    rng = random.Random(seed)
    cycle = 0
    buffer = []                 # pending store finish times
    busy_until = 0              # when memory is free
    for _ in range(N):
        cycle += 1
        buffer = [t for t in buffer if t > cycle]     # remove completed stores
        if rng.random() < f:
            if len(buffer) == B:                      # wait for the oldest store
                cycle = buffer[0]
                buffer.pop(0)
            lat = l_miss if rng.random() < m else l_hit
            start = max(cycle, busy_until)            # FIFO order
            busy_until = start + lat
            buffer.append(busy_until)
    return cycle / N


def simulate_stall(f, m, l_hit, l_miss, seed=SEED):
    rng = random.Random(seed)
    cycle = 0
    for _ in range(N):
        cycle += 1
        if rng.random() < f:
            cycle += l_miss if rng.random() < m else l_hit
    return cycle / N


def main():
    print("Part 1: back-of-envelope CPI = 1 + f * L (every store stalls)")
    print("%6s %6s %8s" % ("f", "L", "CPI"))

    for f in (0.05, 0.10, 0.20):
        for L in (4, 100, 300):
            print("%6.2f %6d %8.2f" % (f, L, 1 + f * L))

    f, m, l_hit, l_miss = 0.10, 0.05, 4, 100
    avg = (1 - m) * l_hit + m * l_miss

    print("\nPart 2: simulation, f = %.2f, miss rate m = %.2f, "
          "L_hit = %d, L_miss = %d" % (f, m, l_hit, l_miss))
    
    print("average store latency = %.1f cycles; formula for stall design "
          "gives CPI = %.2f" % (avg, 1 + f * avg))
    
    print("stall design, simulated: CPI = %.3f"
          % simulate_stall(f, m, l_hit, l_miss))
    
    print("%8s %10s" % ("B", "CPI"))

    for B in (1, 2, 4, 8, 16, 32, 56):
        print("%8d %10.3f" % (B, simulate(f, m, l_hit, l_miss, B)))

    print("\nPart 3: when stores arrive faster than memory can finish them")

    f2, m2 = 0.20, 0.10
    avg2 = (1 - m2) * l_hit + m2 * l_miss

    print("f = %.2f, m = %.2f: average store latency %.1f, f x latency = %.2f"
          % (f2, m2, avg2, f2 * avg2))
    
    print("stall design, simulated: CPI = %.3f"
          % simulate_stall(f2, m2, l_hit, l_miss))
    
    for B in (8, 56):
        print("buffer B = %2d: CPI = %.3f" % (B, simulate(f2, m2, l_hit,
                                                           l_miss, B)))


if __name__ == "__main__":
    main()
