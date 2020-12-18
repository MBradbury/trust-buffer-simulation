#!/usr/bin/env python3
from __future__ import annotations

import pickle
import subprocess
import multiprocessing
import functools
from pprint import pprint
import math
import bz2
import tqdm
import os

from utils.graphing import savefig
from simulation.capability_behaviour import InteractionObservation
from simulation.metrics import Metrics

from pygraphviz import *

def graph_buffer(metrics: Metrics, path_prefix: str, n, total_n, tb):
    print(f"{n}/{total_n}")

    p = AGraph(label=f"({tb.source} {tb.capability}) generating task, utility={tb.utility}")

    # Add agents and capabilities
    for agent in metrics.agent_names:
        for capability in metrics.capability_names:
            if capability == tb.capability:

                if agent == tb.source:
                    p.add_node(f"{agent} {capability}", color="blue", penwidth=4)

                elif tb.outcomes[agent] == InteractionObservation.Incorrect:
                    p.add_node(f"{agent} {capability}", color="red", penwidth=4)

                elif tb.outcomes[agent] == InteractionObservation.Correct:
                    p.add_node(f"{agent} {capability}", color="green", penwidth=4)

                else:
                    raise RuntimeError()

            else:
                if agent == tb.source:
                    p.add_node(f"{agent} {capability}", color="cornflowerblue", penwidth=4)
                else:
                    p.add_node(f"{agent} {capability}", color="grey", penwidth=4)

        p.add_subgraph([f"{agent} {capability}" for capability in metrics.capability_names], name=f"cluster_{agent}")

    # Add buffer nodes

    buffer_sizes = {
        "crypto": metrics.args.max_crypto_buf,
        "trust": metrics.args.max_trust_buf,
        "reputation": metrics.args.max_reputation_buf,
        "stereotype": metrics.args.max_stereotype_buf,
    }

    buffer_colours = {
        "crypto": "darkorchid1",
        "trust": "darkkhaki",
        "reputation": "darkseagreen3",
        "stereotype": "darkslategray2",
    }

    for (name, items) in tb.buffers.items():

        # The items will be shorter than their maximum capacity, so lets add it in now:
        true_size = buffer_sizes[name]

        for i in range(true_size):
            p.add_node(f"{name} {i}", shape="square", color=buffer_colours[name], penwidth=3)

        p.add_subgraph([f"{name} {i}" for i in range(true_size)], name=f"cluster_{name}")

        if name == "crypto":
            for (i, item) in enumerate(items):
                for capability in metrics.capability_names:
                    p.add_edge(f"{name} {i}", f"{item[0]} {capability}", color=buffer_colours[name], penwidth=3)

        elif name == "trust":
            for (i, item) in enumerate(items):
                p.add_edge(f"{name} {i}", f"{item[0]} {item[1]}", color=buffer_colours[name], penwidth=3)

        elif name == "stereotype":
            for (i, item) in enumerate(items):
                p.add_edge(f"{name} {i}", f"{item[0]} {item[1]}", color=buffer_colours[name], penwidth=3)

        elif name == "reputation":
            for (i, (a, alinks)) in enumerate(items):
                for alink in alinks:
                    p.add_edge(f"{name} {i}", f"{alink[0]} {alink[1]}", color=buffer_colours[name], penwidth=3)

        else:
            pass

    pad = math.ceil(math.log10(total_n))
      
    p.layout("sfdp")
    #p.layout("neato")
    p.draw(f'{path_prefix}Topology-{str(n).zfill(pad)}-{tb.t}.pdf')


def graph_buffer_direct(metrics: Metrics, path_prefix: str, n, total_n, tb):
    p = AGraph(label=f"({tb.source} {tb.capability}) generating task, utility={tb.utility}")

    # Add buffer nodes

    buffer_sizes = {
        "crypto": metrics.args.max_crypto_buf,
        "trust": metrics.args.max_trust_buf,
        "reputation": metrics.args.max_reputation_buf,
        "stereotype": metrics.args.max_stereotype_buf,
    }

    buffer_colours = {
        "crypto": "darkorchid1",
        "trust": "darkkhaki",
        "reputation": "darkseagreen3",
        "stereotype": "darkslategray2",
    }

    def edge_colour(x):
        agent, capability = x

        if capability == tb.capability:
            if tb.outcomes[agent] == InteractionObservation.Incorrect:
                return "red"
            elif tb.outcomes[agent] == InteractionObservation.Correct:
                return "green"
            else:
                return None

        else:
            if agent == tb.source:
                return "cornflowerblue"
            else:
                return "grey"

    for (name, items) in tb.buffers.items():

        # The items will be shorter than their maximum capacity, so lets add it in now:
        true_size = buffer_sizes[name]

        for i in range(true_size):
            p.add_node(f"{name} {i}", shape="square", color=buffer_colours[name], penwidth=3)

        p.add_subgraph([f"{name} {i}" for i in range(true_size)], name=f"cluster_{name}")

        if name == "crypto":
            items = [(i, (item[0], capability)) for (i, item) in enumerate(items) for capability in metrics.capability_names]
        elif name == "reputation":
            items = [(i, uitem) for (i, (usrc, uitems)) in enumerate(items) for uitem in uitems]
        else:
            items = list(enumerate(items))

        for (nameb, itemsb) in tb.buffers.items():
            if name == nameb:
                continue

            # Only want links with crypto
            if nameb != "crypto":
                continue

            if nameb == "crypto":
                itemsb = [(i, (item[0], capability)) for (i, item) in enumerate(itemsb) for capability in metrics.capability_names]
            elif nameb == "reputation":
                itemsb = [(i, uitem) for (i, (usrc, uitems)) in enumerate(itemsb) for uitem in uitems]
            else:
                itemsb = list(enumerate(itemsb))

            for (a, itema) in items:
                for (b, itemb) in itemsb:

                    assert itema[0][0] == "A"
                    assert itema[1][0] == "C"

                    assert itemb[0][0] == "A"
                    assert itemb[1][0] == "C"

                    if itema == itemb:
                        p.add_edge(f"{name} {a}", f"{nameb} {b}", label=f"{itema[0]} {itema[1]}", color=edge_colour(itema), penwidth=2)

    pad = math.ceil(math.log10(total_n))

    p.layout("sfdp")
    #p.layout("neato")
    p.draw(f'{path_prefix}Topology-{str(n).zfill(pad)}-{tb.t}.pdf')

def call(fn):
    fn()

def main(args):
    with bz2.open(args.metrics_path, "rb") as f:
        metrics = pickle.load(f)

    fns = [
        functools.partial(graph_buffer_direct, metrics, args.path_prefix, n, len(metrics.buffers), b)
        for (n, b) in enumerate(metrics.buffers)
    ]

    usable_cpus = len(os.sched_getaffinity(0))

    print(f"Running with {usable_cpus} processes")

    with multiprocessing.Pool(usable_cpus) as pool:
        for _ in tqdm.tqdm(pool.imap_unordered(call, fns), total=len(fns)):
            pass

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Analyse')
    parser.add_argument('metrics_path', type=str,
                        help='The path to the metrics to analyse')

    parser.add_argument('--path-prefix', type=str, default="",
                        help='The prefix to the location to output results')

    args = parser.parse_args()

    main(args)
