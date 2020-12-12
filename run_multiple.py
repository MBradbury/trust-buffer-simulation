#!/usr/bin/env python3

from multiprocessing.pool import ThreadPool
import random
import subprocess

def fn(seed):
	print(f"Running {seed}")
	subprocess.run(f"SEED={seed} nice -n 15 ./run.sh", shell=True, check=True)

rng = random.SystemRandom()

with ThreadPool(12) as p:
	seeds = [rng.getrandbits(31) for _ in range(1000)]

	p.map(fn, seeds)
