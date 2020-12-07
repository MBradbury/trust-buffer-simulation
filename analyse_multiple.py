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
from collections import defaultdict

import numpy as np
from scipy.stats import describe

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from simulation.metrics import Metrics
from simulation.capability import CapabilityBehaviourState, InteractionObservation

from analysis import savefig

plt.rcParams['text.usetex'] = True
plt.rcParams['font.size'] = 12

def graph_utility_summary(all_metrics: Dict[str, Metrics], path_prefix: str):

    all_utilities = {
        path.split("-")[0]: [b.utility / b.max_utility for b in metrics.buffers if not np.isnan(b.utility)]
        for (path, metrics) in all_metrics.items()
    }

    labels, Xs = zip(*sorted(all_utilities.items(), key=lambda x: x[0]))

    fig = plt.figure()
    ax = fig.gca()

    ax.boxplot(Xs, labels=labels)

    ax.set_ylim(0, 1)
    ax.set_ylabel('Utility (\\%)')
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, symbol=''))

    ax.set_xticklabels(labels, rotation='vertical')

    savefig(fig, f"{path_prefix}utility-boxplot.pdf")

    plt.close(fig)
    gc.collect()

def graph_utility_summary_grouped_es(all_metrics: Dict[str, Metrics], path_prefix: str):

    print(len(all_metrics))

    behaviours = list(sorted({path[0] for path in all_metrics.keys()}))
    sizes = list(sorted({path[-1] for path in all_metrics.keys()}))

    print(behaviours)
    print(sizes)

    for behaviour, size in itertools.product(behaviours, sizes):
        print(behaviour, size)

        all_utilities = {
            path[1]: [b.utility / b.max_utility for b in metrics.buffers if not np.isnan(b.utility)]
            for (path, metrics) in all_metrics.items()
            if path[0] == behaviour
            and path[-1] == size
        }

        labels, Xs = zip(*sorted(all_utilities.items(), key=lambda x: x[0]))

        fig = plt.figure()
        ax = fig.gca()

        ax.boxplot(Xs, labels=labels)

        ax.set_ylim(0, 1)
        ax.set_ylabel('Normalised Utility (\\%)')
        ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, symbol=''))

        ax.set_xticklabels(labels, rotation='vertical')

        savefig(fig, f"{path_prefix}utility-boxplot-{behaviour}-{size}.pdf")

        plt.close(fig)
        gc.collect()

def metrics_agents_capabilities(metrics: Metrics) -> tuple:
    num_agents = sum(num_agents for (num_agents, behaviour) in args.agents)
    num_capabilities = metrics.args.num_capabilities

    return (num_agents, num_capabilities)

def metrics_capacity(metrics: Metrics) -> float:
    num_agents = metrics.num_agents()
    num_capabilities = metrics.num_capabilities()

    max_crypto_buf = metrics.args.max_crypto_buf
    max_trust_buf = metrics.args.max_trust_buf
    max_reputation_buf = metrics.args.max_reputation_buf
    max_stereotype_buf = metrics.args.max_stereotype_buf

    crypto_capacity = min(1, max_crypto_buf / (num_agents - 1))
    trust_capacity = min(1, max_trust_buf / ((num_agents - 1) * num_capabilities))
    reputation_capacity = min(1, max_reputation_buf / (num_agents - 1))
    stereotype_capacity = min(1, max_stereotype_buf / ((num_agents - 1) * num_capabilities))

    return (crypto_capacity + trust_capacity + reputation_capacity + stereotype_capacity) / 4


def graph_capacity_utility_es(all_metrics: Dict[str, Metrics], path_prefix: str):

    print(len(all_metrics))

    behaviours = list(sorted({path[0] for path in all_metrics.keys()}))
    strategies = list(sorted({path[1] for path in all_metrics.keys()}))
    sizes = list(sorted({path[-1] for path in all_metrics.keys()}))

    print(behaviours)
    print(strategies)
    print(sizes)

    data = []

    for behaviour, size in itertools.product(behaviours, sizes):
        print(behaviour, size)

        data.extend(
            (metrics_capacity(metrics), behaviour, path[1], np.median([b.utility / b.max_utility for b in metrics.buffers if not np.isnan(b.utility)]))
            for (path, metrics) in all_metrics.items()
            if path[0] == behaviour
            and path[-1] == size
        )

    for behaviour in behaviours:
        fig = plt.figure()
        ax = fig.gca()

        for strategy in strategies:
            d = [(x, y) for (x, b, s, y) in data if s == strategy and b == behaviour]

            X, Y = zip(*d)

            ax.scatter(X, Y, label=strategy)

        ax.set_ylim(0 - 0.05, 1 + 0.05)
        ax.set_ylabel('Median Normalised Utility (\\%)')
        ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, symbol=''))

        ax.set_xlim(1 + 0.05, 0 - 0.05)
        ax.set_xlabel('Capacity (\\%)')
        ax.xaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, symbol=''))

        ax.legend()

        savefig(fig, f"{path_prefix}capacity-utility-scatter-{behaviour}.pdf")

        plt.close(fig)
        gc.collect()

def graph_size_utility_es(all_metrics: Dict[str, Metrics], path_prefix: str):

    print(len(all_metrics))

    behaviours = list(sorted({path[0] for path in all_metrics.keys()}))
    sizes = list(sorted({path[-1] for path in all_metrics.keys()}))

    print(behaviours)
    print(sizes)

    fig, axs = plt.subplots(nrows=len(behaviours), ncols=len(sizes), sharey=True, figsize=(20, 18))

    for (i, behaviour) in enumerate(behaviours):

        for (j, size) in enumerate(sizes):
            print(behaviour, size)

            ax = axs[i, j]

            data = [
                #(behaviour, size, path[1], describe())

                (path[1], np.quantile([b.utility / b.max_utility for b in metrics.buffers if not np.isnan(b.utility)], [0.25,0.5,0.75]))

                for (path, metrics) in all_metrics.items()
                if path[0] == behaviour
                and path[-1] == size
            ]

            X, Y = zip(*data)
            Ydata = [x for (_, x, _) in Y]
            Yerr = [(x - l, u - x) for (l, x, u) in Y]

            mplyerr = list(zip(*Yerr))

            ax.bar(X, Ydata, yerr=mplyerr)

            if j == 0:
                
                ax.set_ylabel('Median Utility (\\%)')
            ax.set_ylim(0, 1)
            ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, symbol=''))

            ax.set_xticklabels(X, rotation='vertical')

            ax.set_title(behaviour.title() + " " + size.title())

    savefig(fig, f"{path_prefix}capacity-utility-bar.pdf")

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

    fns = [graph_capacity_utility_es, graph_utility_summary_grouped_es]
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
