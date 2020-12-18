#!/usr/bin/env python3
from __future__ import annotations

import os
import bz2
import fnmatch
from pprint import pprint
from dataclasses import dataclass
import multiprocessing
import pickle
import tqdm

import numpy as np

class ParametersDifferError(RuntimeError):
    def __init__(self, self_args, m_args):
        self_args_dict = vars(self_args)
        self.params_diff_m_args = {k: v for (k, v) in vars(m_args).items() if k not in self_args_dict or self_args_dict[k] != v}
        self.params_diff_self_args = {k: v for (k, v) in self_args_dict if k in self.params_diff_m_args}

        super().__init__(f"Parameters differ m_args={self.params_diff_m_args}, self_args={self.params_diff_self_args}")

class CombinedMetrics:
    def __init__(self):
        self.normed_utilities = []
        self.args = None

    def update(self, m: Metrics):
        if self.args is None:
            self.args = m.args
            self.args.seed = None
        else:
            m.args.seed = None
            if self.args != m.args:
                raise ParametersDifferError(self.args, m.args)

        self.normed_utilities.extend([b.utility / b.max_utility for b in m.buffers if not np.isnan(b.utility)])

    def finish(self):
        pass

    def num_agents(self) -> int:
        return sum(num_agents for (num_agents, behaviour) in self.args.agents)

    def num_capabilities(self) -> int:
        return self.args.num_capabilities

def fn(args):
    (metrics_dir, prefix, files) = args

    print(f"Processing {metrics_dir} {prefix} {len(files)} files...")

    m = CombinedMetrics()

    for file in files:
        path = os.path.join(metrics_dir, file)
        with bz2.open(path, "rb") as f:
            try:
                m.update(pickle.load(f))
            except EOFError as ex:
                # Corrupted pickle
                print(f"{ex} for {path}")
                print("Skipping...")
                continue
            except ParametersDifferError as ex:
                print(f"{ex} for {path}")
                raise

    # Replace the seed number with combined
    target_file = list(files[0].split("."))
    target_file[1] = "combined"
    target_file = ".".join(target_file)

    target_path = os.path.join(metrics_dir, target_file)
    print(f"Saving result to {target_path}")

    m.finish()

    with bz2.open(target_path, "wb") as f:
        pickle.dump(m, f)

def main(args):
    metrics_paths = {
        metrics_dir: [
            file
            for file in os.listdir(metrics_dir)
            if fnmatch.fnmatch(file, "*.pickle.bz2")
            and "combined" not in file
        ]
        for metrics_dir in args.metrics_dirs
    }

    new_metrics_paths = {}

    # Now need to group the results
    for (metrics_dir, files) in metrics_paths.items():
        new_metrics_paths[metrics_dir] = {}

        prefixes = {file.split("-")[0] for file in files}

        for prefix in prefixes:
            selected_files = [file for file in files if file.startswith(prefix + "-")]

            new_metrics_paths[metrics_dir][prefix] = selected_files

    args = [
        (metrics_dir, prefix, files)

        for (metrics_dir, prefix_files) in new_metrics_paths.items()
        for (prefix, files) in prefix_files.items()
    ]

    new_nice = os.nice(10)
    print(f"Niceness set to {new_nice}")

    usable_cpus = len(os.sched_getaffinity(0))

    print(f"Running with {usable_cpus} processes")

    with multiprocessing.Pool(usable_cpus) as pool:
        for _ in tqdm.tqdm(pool.imap_unordered(fn, args), total=len(args)):
            pass

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Analyse')
    parser.add_argument('metrics_dirs', type=str, nargs="+",
                        help='The path to the directory of metrics to analyse')

    args = parser.parse_args()

    main(args)
