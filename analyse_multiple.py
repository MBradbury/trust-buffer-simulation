#!/usr/bin/env python3
from __future__ import annotations

import pickle
import subprocess
import itertools
from itertools import chain
from multiprocessing import Pool
import functools
from pprint import pprint
import os
import fnmatch
from typing import Dict
import gc

import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt

from simulation.metrics import Metrics
from simulation.capability import CapabilityBehaviourState, InteractionObservation

from analysis import savefig

plt.rcParams['text.usetex'] = True
plt.rcParams['font.size'] = 12

def graph_utility_summary(all_metrics: Dict[str, Metrics], path_prefix: str):

    all_utilities = {
        path.split("-")[0]: [b.utility for b in metrics.buffers if not np.isnan(b.utility)]
        for (path, metrics) in all_metrics.items()
    }

    labels, Xs = zip(*sorted(all_utilities.items(), key=lambda x: x[0]))

    fig = plt.figure()
    ax = fig.gca()

    ax.boxplot(Xs, labels=labels)

    #ax.set_ylim(0, 1)
    ax.set_ylabel('Utility (\\%)')

    ax.set_xticklabels(ax.get_xticklabels(), rotation='vertical')

    savefig(fig, f"{path_prefix}utility-boxplot.pdf")


def graph_utility_summary_grouped_es(all_metrics: Dict[str, Metrics], path_prefix: str):

    print(len(all_metrics))

    behaviours = list(sorted({path[0] for path in all_metrics.keys()}))
    sizes = list(sorted({path[-1] for path in all_metrics.keys()}))

    print(behaviours)
    print(sizes)

    for behaviour, size in itertools.product(behaviours, sizes):
        #eviction_strategies = {metrics.args.eviction_strategy for metrics in all_metrics.values()}

        print(behaviour, size)

        all_utilities = {
            path[1]: [b.utility for b in metrics.buffers if not np.isnan(b.utility)]
            for (path, metrics) in all_metrics.items()
            if path[0] == behaviour
            and path[-1] == size
        }

        labels, Xs = zip(*sorted(all_utilities.items(), key=lambda x: x[0]))

        fig = plt.figure()
        ax = fig.gca()

        ax.boxplot(Xs, labels=labels)

        ax.set_ylim(0, 1)
        ax.set_ylabel('Utility (\\%)')

        ax.set_xticklabels(ax.get_xticklabels(), rotation='vertical')

        savefig(fig, f"{path_prefix}utility-boxplot-{behaviour}-{size}.pdf")

        plt.close(fig)
        gc.collect()

# from: http://louistiao.me/posts/adding-__name__-and-__doc__-attributes-to-functoolspartial-objects/
def wrapped_partial(func, *args, **kwargs):
    partial_func = functools.partial(func, *args, **kwargs)
    functools.update_wrapper(partial_func, func)
    return partial_func

def call(fn):
    print(f"Running {fn.__name__}")
    fn()

def metrics_path_to_details(path):
    spath = list(path.split("/"))

    spath[-1] = spath[-1].split("-")[0]

    return tuple(spath)

def main(args):
    metrics_paths = [
        f"{metrics_dir}/{file}"
        for metrics_dir in args.metrics_dirs
        for file in os.listdir(metrics_dir)
        if fnmatch.fnmatch(f"{metrics_dir}/{file}", "*.pickle")
    ]

    all_metrics = {}

    print("Loading metrics...")

    for metrics_path in metrics_paths:
        with open(metrics_path, "rb") as f:
            all_metrics[metrics_path_to_details(metrics_path)] = pickle.load(f)

    print("Loaded metrics!")

    fns = [graph_utility_summary_grouped_es]
    fns = [wrapped_partial(fn, all_metrics, args.path_prefix) for fn in fns]

    print("Creating graphs...")

    #with Pool(4) as p:
    #    p.map(call, fns)
    for fn in fns:
        call(fn)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Analyse')
    parser.add_argument('metrics_dirs', type=str, nargs="+",
                        help='The path to the directory of metrics to analyse')

    parser.add_argument('--path-prefix', type=str, default="",
                        help='The prefix to the location to output results')

    args = parser.parse_args()

    main(args)
