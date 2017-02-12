#! /usr/bin/env python
from __future__ import print_function
from atlasseq.graph import ProbabilisticMultiColourDeBruijnGraph as Graph
import argparse
import json
import pickle


def samples(sample_name, graph):
    if sample_name is None:
        out = {}
        for colour, sample_name in graph.colours_to_sample_dict().items():
            if not sample_name in out:
                out[sample_name] = {}
            out[sample_name]["colour"] = int(colour)
            out[sample_name]["name"] = sample_name
            # out[sample_name]["kmer_count"] = graph.count_kmers(sample_name)
    else:
        out = {sample_name: {}}
        out[sample_name]["colour"] = graph.get_colour_from_sample(sample_name)
        out[sample_name]["name"] = sample_name
        # out[sample_name]["kmer_count"] = graph.count_kmers(sample_name)

    return out
