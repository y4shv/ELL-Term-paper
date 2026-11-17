#!/bin/sh
# Run the Chapter 7 hardware configurations.
# Each configuration runs REPEATS times, with ITER iterations per run.
# Results: results/litmus_raw.csv
set -e
cd "$(dirname "$0")"
gcc -O2 -Wall -pthread -o litmus litmus.c
ITER=1000000
REPEATS=10
OUT=../results/litmus_raw.csv
echo "test,skew,repeat,iterations,c00,c01,c10,c11" > $OUT
run() {  # test and skew
    for r in $(seq 1 $REPEATS); do
        line=$(./litmus "$1" $ITER "$2")
        c00=$(echo "$line" | sed 's/.*(0,0)=\([0-9]*\).*/\1/')
        c01=$(echo "$line" | sed 's/.*(0,1)=\([0-9]*\).*/\1/')
        c10=$(echo "$line" | sed 's/.*(1,0)=\([0-9]*\).*/\1/')
        c11=$(echo "$line" | sed 's/.*(1,1)=\([0-9]*\).*/\1/')
        echo "$1,$2,$r,$ITER,$c00,$c01,$c10,$c11" >> $OUT
    done
}
for s in 0 10 25 50 100 200; do run sb $s; done
for s in 0 25 50; do run sb_mfence $s; done
for s in 0 25 50; do run mp $s; done
echo "done: $OUT"
