#! /usr/bin/env python
from __future__ import print_function
import sys
import os
import argparse
import redis
import json
import math
import logging
import hug
import tempfile
import humanfriendly
import yaml

from bigsi.version import __version__
from bigsi.graph import BIGSI

from bigsi.cmds.insert import insert
from bigsi.cmds.search import search
from bigsi.cmds.samples import samples
from bigsi.cmds.delete import delete
from bigsi.cmds.bloom import bloom
from bigsi.cmds.build import build
from bigsi.cmds.merge import merge
from bigsi.utils.cortex import extract_kmers_from_ctx

from bigsi.utils import seq_to_kmers


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


API = hug.API("bigsi-%s" % str(__version__))


def get_config_from_file(config_file):
    if config_file is None:
        config = DEFAULT_CONFIG
    else:
        with open(config_file, "r") as infile:
            config = yaml.load(infile)
    return config


@hug.object(name="bigsi", version="0.1.1", api=API)
@hug.object.urls("/", requires=())
class bigsi(object):
    @hug.object.cli
    @hug.object.post("/insert", output_format=hug.output_format.json)
    def insert(self, db: hug.types.text, bloomfilter, sample, i: int = 1, N: int = 1):
        """Inserts a bloom filter into the graph

        e.g. bigsi insert ERR1010211.bloom ERR1010211

        """
        index = BIGSI(db)
        bf_range = bf_range_calc(index, i, N)

        return insert(
            graph=index, bloomfilter=bloomfilter, sample=sample, bf_range=bf_range
        )

    @hug.object.cli
    @hug.object.post("/bloom")
    def bloom(self, outfile, config=None, ctx=None):
        """Creates a bloom filter from a sequence file or cortex graph. (fastq,fasta,bam,ctx)

        e.g. index insert ERR1010211.ctx

        """
        config = get_config_from_file(config)
        bf = bloom(
            config=config,
            outfile=outfile,
            kmers=extract_kmers_from_ctx(ctx, config["k"]),
        )

    @hug.object.cli
    @hug.object.post("/build", output_format=hug.output_format.json)
    def build(
        self,
        config: hug.types.text,
        bloomfilters: hug.types.multiple,
        samples: hug.types.multiple = [],
    ):
        config = get_config_from_file(config)

        if samples:
            assert len(samples) == len(bloomfilters)
        else:
            samples = bloomfilters

        if config.get("max_build_mem_bytes"):
            max_memory_bytes = humanfriendly.parse_size(config["max_build_mem_bytes"])
        else:
            max_memory_bytes = None

        return build(
            config=config,
            bloomfilter_filepaths=bloomfilters,
            samples=samples,
            max_memory=max_memory_bytes,
        )

    @hug.object.cli
    @hug.object.post("/merge", output_format=hug.output_format.json)
    def merge(self, db1: hug.types.text, db2: hug.types.text):
        BIGSI(db1).merge(BIGSI(db2))
        return {"result": "merged %s into %s." % (db2, db1)}

    @hug.object.cli
    @hug.object.get(
        "/search",
        examples="seq=ACACAAACCATGGCCGGACGCAGCTTTCTGA",
        output_format=hug.output_format.json,
        response_headers={"Access-Control-Allow-Origin": "*"},
    )
    # @do_cprofile
    def search(
        self,
        config: hug.types.text = None,
        seq: hug.types.text = None,
        threshold: hug.types.float_number = 1.0,
    ):
        config = get_config_from_file(config)
        bigsi = BIGSI(config)
        return bigsi.search(seq, threshold)

    @hug.object.cli
    @hug.object.delete("/", output_format=hug.output_format.json)
    def delete(self, config: hug.types.text = None):
        config = get_config_from_file(config)
        try:
            bigsi = BIGSI(config)
        except ValueError:
            pass
        else:
            return bigsi.delete()

    # @hug.object.cli
    # @hug.object.get('/graph', output_format=hug.output_format.json)
    # def stats(self):
    #     return stats(graph=get_graph())

    @hug.object.cli
    @hug.object.get("/samples", output_format=hug.output_format.json)
    def samples(
        self,
        sample_name: hug.types.text = None,
        db: hug.types.text = None,
        delete: hug.types.smart_boolean = False,
    ):
        return samples(sample_name, graph=get_graph(bdb_db_filename=db), delete=delete)

    # @hug.object.cli
    # @hug.object.post('/dump', output_format=hug.output_format.json)
    # def dump(self, filepath):
    #     r = dump(graph=get_graph(), file=filepath)
    #     return r

    # @hug.object.cli
    # @hug.object.post('/load', output_format=hug.output_format.json)
    # def load(self, filepath):
    #     r = load(graph=get_graph(), file=filepath)
    #     return r


def main():
    API.cli()


if __name__ == "__main__":
    main()
