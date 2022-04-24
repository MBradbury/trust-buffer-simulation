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

import more_itertools

def check_fonts(path: str):
    r = subprocess.run(f"pdffonts {path}",
        shell=True,
        check=True,
        capture_output=True,
        universal_newlines=True,
        encoding="utf-8",
    )

    if "Type 3" in r.stdout:
        raise RuntimeError(f"Type 3 font in {path}")

buffer_colours = {
    "crypto": "#9467BD", #"darkorchid1",
    "trust": "#1F77B4", #"darkkhaki",
    "reputation": "#FF7F0E", #darkseagreen3",
    "stereotype": "#BCBD22", #"darkslategray2",
}

def graph_buffer_direct(metrics: Metrics, path_prefix: str, n: int, total_n: int, tb):
    p = AGraph(
        label=f"({tb.source} {tb.capability}) generating task, utility={tb.utility}",
        margin="0",
        #ratio="compress",
        #overlap="voronoi",
        splines="curved",
        outputorder="edgesfirst",
        K=0.125,
        fontsize=22,
        pack=True,
        overlap="prism", overlap_scaling=0.6, ratio=0.5,
        fontname="Adobe Times",
    )

    node_sizes = {
        "crypto": {"fixedsize": "true", "height": "1.2", "width": "1.5"},
        "trust": {"fixedsize": "true", "height": "1.2", "width": "1.5"},
        "reputation": {},
        "stereotype": {"fixedsize": "true", "height": "1.2", "width": "2"},
    }

    text_font_size = 22

    buffer_sizes = {
        "crypto": metrics.args.max_crypto_buf,
        "trust": metrics.args.max_trust_buf,
        "reputation": metrics.args.max_reputation_buf,
        "stereotype": metrics.args.max_stereotype_buf,
    }

    def edge_colour(x):
        agent, capability = x

        if capability == tb.capability:
            if tb.outcomes[agent] == InteractionObservation.Incorrect:
                return "#D62728"
            elif tb.outcomes[agent] == InteractionObservation.Correct:
                return "#2CA02C"
            else:
                return None

        else:
            if agent == tb.source:
                return "#17BECF"
            else:
                return "#7F7F7F"

    def format_item_label(name, x):
        if name == "crypto":
            return x[0]
        elif name == "reputation":
            # This one is a pain as it can be quite long
            result = f"Provided by: {x[0]}\\n"

            if len(x[1]) < 2:
                [curr_item] = x[1]
                result += f"- {curr_item[0]} {curr_item[1]}"
            else:
                reputation_items = []
                skip_next = False
                for (curr_item, next_item) in more_itertools.pairwise(sorted(x[1])):
                    if skip_next:
                        skip_next = False
                        continue

                    if curr_item[0] == next_item[0] and curr_item[1] != next_item[1]:
                        reputation_items.append(f"- {curr_item[0]} {curr_item[1]} - {next_item[0]} {next_item[1]}")
                        skip_next = True
                    else:
                        reputation_items.append(f"- {curr_item[0]} {curr_item[1]}")

                result += "\\n".join(reputation_items) #+ "\nActual:\n" + "\n".join(str(x) for x in sorted(x[1]))
            return result
        else:
            return f"{x[0]} {x[1]}"

    for (name, items) in tb.buffers.items():

        # The items will be shorter than their maximum capacity, so lets add it in now:
        true_size = buffer_sizes[name]

        sp = p # p.add_subgraph(name=f"cluster_{name}", label=name.title())

        for i in range(true_size):
            style = {
                "color": buffer_colours[name],
                "penwidth": 4,
                "shape": "square",
                "style": "rounded",
                "fontsize": text_font_size,
                **node_sizes[name],
            }

            # Fill the node in if it contains a value
            if i < len(items):
                style["fillcolor"] = "#DDDDDDD0"
                style["style"] = "rounded,filled"
                style["label"] = f"{name} {i}\\n{format_item_label(name, items[i])}"

            sp.add_node(f"{name} {i}", **style)

        # Don't want links from crypto
        if name == "crypto":
            continue
            
        if name == "reputation":
            items = [(i, uitem) for (i, (usrc, uitems)) in enumerate(items) for uitem in uitems]
        else:
            items = list(enumerate(items))

        for (nameb, itemsb) in tb.buffers.items():
            if name == nameb:
                continue

            # Only want links with crypto
            if nameb != "crypto":
                continue

            itemsb = [(i, (item[0], capability)) for (i, item) in enumerate(itemsb) for capability in metrics.capability_names]

            for (a, itema) in items:
                for (b, itemb) in itemsb:

                    assert itema[0][0] == "A"
                    assert itema[1][0] == "C"

                    assert itemb[0][0] == "A"
                    assert itemb[1][0] == "C"

                    if itema == itemb:
                        sp.add_edge(f"{name} {a}", f"{nameb} {b}", color=edge_colour(itema), penwidth=2) # label=f"{itema[0]} {itema[1]}", 

    pad = math.ceil(math.log10(total_n))

    output_file = f'{path_prefix}Topology-{str(n).zfill(pad)}-{tb.t}.pdf'

    p.layout("neato")
    #p.layout("dot")
    p.draw(output_file)
    #p.draw(output_file[:-4] + ".gv")
    #p.draw(output_file[:-4] + ".svg")

    subprocess.run(f"pdfcrop {output_file} {output_file}", check=True, shell=True, stdout=subprocess.DEVNULL)

    check_fonts(output_file)

def graph_legend(metrics: Metrics, path_prefix: str):
    text_font_size = 20

    p = AGraph(
        margin="0",
        n=2,
        forcelabels=True,
        fontsize=text_font_size,
        label=f"Agent A0 generating task for service C0, A1 behaves correctly, A2 behaves incorrectly",
        fontname="Adobe Times",
    )

    node_sizes = {
        "crypto": {"fixedsize": "true", "height": "1.2", "width": "1.5"},
        "trust": {"fixedsize": "true", "height": "1.2", "width": "1.5"},
        "reputation": {},
        "stereotype": {"fixedsize": "true", "height": "1.2", "width": "2"},
    }

    # Nodes
    for (i, name) in enumerate(buffer_colours.keys()):
        style = {
            "color": buffer_colours[name],
            "penwidth": 4,
            "shape": "square",
            "style": "rounded",
            "fontsize": text_font_size,
            **node_sizes[name],
            "label": f"{name}\\nno data",
            "pos": f"{i*5},0!",
        }

        p.add_node(f"{name} empty", **style)

        style["fillcolor"] = "#DDDDDDD0"
        style["style"] = "rounded,filled"
        style["label"] = f"{name}\\nhas data"
        style["pos"] = f"{i*5 + 2.5},0!"

        p.add_node(f"{name} filled", **style)


    def filled_style(name, i, details, pos):
        return {
            "color": buffer_colours[name],
            "penwidth": 4,
            "shape": "square",
            "style": "rounded,filled",
            "fillcolor": "#DDDDDDD0",
            "fontsize": text_font_size,
            **node_sizes[name],
            "label": f"{name} {i}\\n{details}",
            "pos": pos,
        }

    edge_colours = {
        (True, InteractionObservation.Correct): "#2CA02C",
        (True, InteractionObservation.Incorrect): "#D62728",
        (False, InteractionObservation.Correct): "#7F7F7F",
        #(False, InteractionObservation.Incorrect): "#7F7F7F",
    }

    # Edges
    for (i, ((same, result), edge_colour)) in enumerate(edge_colours.items()):

        agent = "A1" if result == InteractionObservation.Correct else "A2"
        if same:
            label = f"Same service as interaction,\\nbehaves {result.name.lower()}ly"
            capability = "C0"
        else:
            label = "Different service to interaction"
            capability = "C1"


        p.add_node(f"crypto e{i}-1", **filled_style(f"crypto", i, f"{agent}", f"{i*6.5},-2.5!"))
        p.add_node(f"trust e{i}-2", **filled_style(f"trust", i, f"{agent} {capability}", f"{i*6.5 + 6.5/2},-2.5!"))

        p.add_edge(f"crypto e{i}-1", f"trust e{i}-2", color=edge_colour, penwidth=2)

        p.add_node(f"crypto e{i}-text", 
            shape="plaintext",
            fontsize=text_font_size,
            label=label,
            pos=f"{i*6.5 + 6.5/4},-3.75!",
            )

    output_file = f'{path_prefix}legend.pdf'

    p.layout("neato")
    p.draw(output_file)

    subprocess.run(f"pdfcrop {output_file} {output_file}", check=True, shell=True, stdout=subprocess.DEVNULL)

    check_fonts(output_file)

def call(fn):
    fn()

def main(args):
    with bz2.open(args.metrics_path, "rb") as f:
        metrics = pickle.load(f)

    fns = [
        functools.partial(graph_buffer_direct, metrics, args.path_prefix, n, len(metrics.buffers), b)
        for (n, b) in enumerate(metrics.buffers)
        if args.specific is None or n in args.specific
    ]

    usable_cpus = len(os.sched_getaffinity(0))

    print(f"Running with {usable_cpus} processes")

    with multiprocessing.Pool(usable_cpus) as pool:
        for _ in tqdm.tqdm(pool.imap_unordered(call, fns), total=len(fns)):
            pass

    if args.make_legend:
        graph_legend(metrics, args.path_prefix)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Analyse')
    parser.add_argument('metrics_path', type=str,
                        help='The path to the metrics to analyse')

    parser.add_argument('--path-prefix', type=str, default="",
                        help='The prefix to the location to output results')

    parser.add_argument('--specific', nargs="+", default=None, type=int,
                        help='Specific graphs to create')

    parser.add_argument('--make-legend', action="store_true", default=False,
                        help='Create a legend')

    args = parser.parse_args()
    args.specific = None if args.specific is None else set(args.specific)

    main(args)
