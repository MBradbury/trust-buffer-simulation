#!/usr/bin/env python3
from __future__ import annotations

import bz2
import itertools
import functools
import os
import fnmatch
from typing import Dict
import gc
from collections import defaultdict
import pickle

import numpy as np
from scipy.stats import describe
import pandas as pd

import matplotlib as mpl
from matplotlib import cm
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

import seaborn

from utils.graphing import savefig
from combine_results import CombinedMetrics

plt.rcParams['text.usetex'] = True
plt.rcParams['font.size'] = 12

def graph_utility_summary(all_metrics: Dict[str, CombinedMetrics], path_prefix: str):

    all_utilities = {
        path.split("-")[0]: metrics.normed_utilities
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

# From: https://stackoverflow.com/a/61870668
def get_box_plot_data(labels, bp):
    rows_list = []

    for i in range(len(labels)):
        dict1 = {}
        dict1['label'] = labels[i]
        dict1['lower_whisker'] = bp['whiskers'][i*2].get_ydata()[1]
        dict1['lower_quartile'] = bp['boxes'][i].get_ydata()[1]
        dict1['median'] = bp['medians'][i].get_ydata()[1]
        dict1['upper_quartile'] = bp['boxes'][i].get_ydata()[2]
        dict1['upper_whisker'] = bp['whiskers'][(i*2)+1].get_ydata()[1]
        dict1['iqr'] = dict1['upper_quartile'] - dict1['lower_quartile']
        rows_list.append(dict1)

    return pd.DataFrame(rows_list)

def graph_utility_summary_grouped_es(all_metrics: Dict[str, CombinedMetrics], path_prefix: str):

    print(len(all_metrics))

    behaviours = list(sorted({path[0] for path in all_metrics.keys()}))
    sizes = list(sorted({path[-1] for path in all_metrics.keys()}))

    print("behaviours", behaviours)
    print("sizes", sizes)

    color = True
    dfs = {}

    for behaviour, size in itertools.product(behaviours, sizes):
        print(behaviour, size)

        all_utilities = {
            path[1]: metrics.normed_utilities
            for (path, metrics) in all_metrics.items()
            if path[0] == behaviour
            and path[-1] == size
        }

        all_utilities_medians = {
            k: np.median(v)
            for (k, v) in all_utilities.items()
        }

        sorted_labels = list(sorted(all_utilities.keys()))

        labels, Xs = zip(*sorted(all_utilities.items(), key=lambda x: all_utilities_medians[x[0]], reverse=True))

        fig = plt.figure()
        ax = fig.gca()

        bp = ax.boxplot(Xs,
                        labels=labels,
                        showmeans=True,
                        showfliers=False,
                        patch_artist=color,
                        medianprops={"color": "dimgray"},
                        meanprops={"marker":".", "markerfacecolor":"grey", "markeredgecolor":"grey"})

        if color:
            cmap = seaborn.color_palette("husl", n_colors=len(bp['boxes']))

            for i, box in enumerate(bp['boxes']):
                box.set(facecolor="white")
                box.set(edgecolor=cmap[sorted_labels.index(labels[i])], linewidth=2)

        ax.set_ylim(0, 1)
        ax.set_ylabel('Normalised Utility (\\%)')
        ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, symbol=''))
        #ax.yaxis.grid(True)

        ax.set_xticklabels(labels, rotation='vertical')

        savefig(fig, f"{path_prefix}utility-boxplot-{behaviour}-{size}.pdf")

        if not color:
            with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'expand_frame_repr', False): 
                with open(f"{path_prefix}utility-boxplot-{behaviour}-{size}.txt", "w") as f:
                    df = get_box_plot_data(labels, bp)
                    print(df, file=f)

                    dfs[(behaviour, size)] = df

        plt.close(fig)
        gc.collect()


    if not color:
        #max_median_diff = [(df["median"].max(), df["median"].min()) for df in dfs.values()]
        #print("max_median_diff", max_median_diff)

        """for (k, df) in dfs.items():
            print(k)
            print(df.nlargest(5, "median")["median"])
            print()"""

        max_median_diff = [df["median"].max() - df["median"].min() for df in dfs.values()]
        print("max_median_diff", max_median_diff)
        print("max_median_diff", max(max_median_diff))
        print("max_median_diff", np.mean(max_median_diff))

        labels = {"MinNotInother", "NotInOther", "Chen2016", "FiveBand", "FIFO", "LRU", "LRU2", "Random"}

        selected_dfs = [df[df["label"].isin(labels)] for df in dfs.values()]

        print(selected_dfs)

        max_median_diff = [df["median"].max() - df["median"].min() for df in selected_dfs]
        print("max_median_diff", max_median_diff)
        print("max_median_diff", max(max_median_diff))



def metrics_agents_capabilities(metrics: CombinedMetrics) -> tuple:
    num_agents = sum(num_agents for (num_agents, behaviour) in args.agents)
    num_capabilities = metrics.args.num_capabilities

    return (num_agents, num_capabilities)

def metrics_capacity(metrics: CombinedMetrics) -> float:
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


def graph_capacity_utility_es(all_metrics: Dict[str, CombinedMetrics], path_prefix: str):

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
            (metrics_capacity(metrics), behaviour, path[1], np.median(metrics.normed_utilities))
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

def graph_size_utility_es(all_metrics: Dict[str, CombinedMetrics], path_prefix: str):
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
                #(path[1], np.quantile([b.utility / b.max_utility for b in metrics.buffers if not np.isnan(b.utility)], [0.25,0.5,0.75]))
                (path[1], np.quantile(metrics.normed_utilities, [0.25,0.5,0.75]))

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
        if fnmatch.fnmatch(f"{metrics_dir}/{file}", "*.combined.pickle.bz2")
    ]

    all_metrics = {}

    print("Loading metrics...")

    for metrics_path in metrics_paths:
        with bz2.open(metrics_path, "rb") as f:
            all_metrics[metrics_path_to_details(metrics_path)] = pickle.load(f)

    print(f"Loaded {len(all_metrics)} metrics!")

    fns = [graph_utility_summary_grouped_es]
    fns = [wrapped_partial(fn, all_metrics, args.path_prefix) for fn in fns]

    print("Creating graphs...")

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
