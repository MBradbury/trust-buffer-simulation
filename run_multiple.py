#!/usr/bin/env python3

import os
from multiprocessing.pool import ThreadPool
import random
import subprocess

new_nice = os.nice(10)
print(f"Niceness set to {new_nice}")

def fn(seed):
	print(f"Running {seed}")
	subprocess.run(f"SEED={seed} nice -n 15 ./run.sh", shell=True, check=True)

rng = random.SystemRandom()

usable_cpus = len(os.sched_getaffinity(0))

print(f"Running with {usable_cpus} threads")

with ThreadPool(usable_cpus) as p:
	seeds = [rng.getrandbits(31) for _ in range(1000)]

	p.map(fn, seeds)
