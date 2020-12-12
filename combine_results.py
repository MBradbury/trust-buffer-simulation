#!/usr/bin/env python3
from __future__ import annotations

import os
import pickle
import fnmatch
from pprint import pprint
from dataclasses import dataclass
from multiprocessing import Pool

import numpy as np

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
                raise RuntimeError("Parameters differ")

        self.normed_utilities.extend([b.utility / b.max_utility for b in m.buffers if not np.isnan(b.utility)])

    def finish(self):
        pass

    def num_agents(self) -> int:
        return sum(num_agents for (num_agents, behaviour) in self.args.agents)

    def num_capabilities(self) -> int:
        return self.args.num_capabilities

def fn(metrics_dir, prefix, files):
    print(f"Processing {metrics_dir} {prefix} {len(files)} files...")

    m = CombinedMetrics()

    for file in files:
        with open(os.path.join(metrics_dir, file), "rb") as f:
            m.update(pickle.load(f))

    target_file = list(files[0].split("."))
    target_file[1] = "combined"
    target_file = ".".join(target_file)

    target_path = os.path.join(metrics_dir, target_file)
    print(f"Saving result to {target_path}")

    m.finish()

    with open(target_path, "wb") as f:
        pickle.dump(m, f)

def main(args):
    metrics_paths = {
        metrics_dir: [
            file
            for file in os.listdir(metrics_dir)
            if fnmatch.fnmatch(file, "*.pickle")
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
            selected_files = [file for file in files if file.startswith(prefix)]

            new_metrics_paths[metrics_dir][prefix] = selected_files

    args = [
        (metrics_dir, prefix, files)

        for (metrics_dir, prefix_files) in new_metrics_paths.items()
        for (prefix, files) in prefix_files.items()
    ]

    with Pool(8) as p:
        p.starmap(fn, args)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Analyse')
    parser.add_argument('metrics_dirs', type=str, nargs="+",
                        help='The path to the directory of metrics to analyse')

    args = parser.parse_args()

    main(args)
