#!/usr/bin/env python3
from __future__ import annotations

import functools

import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt

from utils.graphing import savefig

plt.rcParams['text.usetex'] = True
plt.rcParams['font.size'] = 12

def graph_space(path_prefix: str):
    fig = plt.figure()
    ax = fig.gca()

    def fn(v, c, t):
        crypto = 160 * v
        #trust = t * v + t * v * c
        trust = t * v * c
        reputation = v * trust
        stereotype = t * v * c

        return crypto + trust + reputation + stereotype

    vcs = [
        (10, 1),
        (10, 2),
        (20, 1),
        (20, 2),
    ]

    Xs = np.arange(1, 44, 1)

    for (v, c) in vcs:
        Ys = np.vectorize(functools.partial(fn, v, c))(Xs)

        ax.plot(Xs, Ys, label=f"$|V|={v}$ $|C|={c}$")

    ax.axhline(y=32*1024, label="Zolertia RE Mote total memory", color="red")
    ax.axhline(y=(32 - 22)*1024, label="Zolertia RE Mote available memory", color="darkred")

    #ax.axhline(y=256*1024, label="nRF52840 total memory", color="red")
    #ax.axhline(y=(256 - 22)*1024, label="nRF52840 available memory", color="darkred")

    ax.axvline(x=8, label="$T$ (BRS)", linestyle="--", color="tab:purple")
    ax.axvline(x=40, label="$T$ (HMM with 2 states, 2 observations)", linestyle="--", color="tab:olive")

    ax.set_xlabel('Trust model size (bytes)')
    ax.set_ylabel('Total size (bytes)')

    ax.set_ylim(top=(32+4)*1024)

    ax.legend(bbox_to_anchor=(0.45, 1.325), loc="upper center", ncol=2)

    savefig(fig, f"{path_prefix}space.pdf")

    plt.close(fig)

def main(args):
    graph_space(args.path_prefix)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Analyse')
    parser.add_argument('--path-prefix', type=str, default="",
                        help='The prefix to the location to output results')

    args = parser.parse_args()

    main(args)
