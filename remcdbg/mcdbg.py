from __future__ import print_function
import redis
import math
from Bio.Seq import Seq
import numpy as np
# set up redis connections
KMER_SHARDING = {}

KMER_SHARDING[0] = {0: ''}
KMER_SHARDING[1] = {0: 'A', 1: 'T', 2: 'C', 3: 'G'}
KMER_SHARDING[2] = {0: 'AA', 1: 'AT', 2: 'AC', 3: 'AG', 4: 'TA', 5: 'TT', 6: 'TC',
                    7: 'TG', 8: 'CA', 9: 'CT', 10: 'CC', 11: 'CG', 12: 'GA', 13: 'GT', 14: 'GC', 15: 'GG'}
KMER_SHARDING[3] = {0: 'AAA', 1: 'AAT', 2: 'AAC', 3: 'AAG', 4: 'ATA', 5: 'ATT', 6: 'ATC', 7: 'ATG', 8: 'ACA', 9: 'ACT', 10: 'ACC', 11: 'ACG', 12: 'AGA', 13: 'AGT', 14: 'AGC', 15: 'AGG', 16: 'TAA', 17: 'TAT', 18: 'TAC', 19: 'TAG', 20: 'TTA', 21: 'TTT', 22: 'TTC', 23: 'TTG', 24: 'TCA', 25: 'TCT', 26: 'TCC', 27: 'TCG', 28: 'TGA', 29: 'TGT', 30: 'TGC', 31:
                    'TGG', 32: 'CAA', 33: 'CAT', 34: 'CAC', 35: 'CAG', 36: 'CTA', 37: 'CTT', 38: 'CTC', 39: 'CTG', 40: 'CCA', 41: 'CCT', 42: 'CCC', 43: 'CCG', 44: 'CGA', 45: 'CGT', 46: 'CGC', 47: 'CGG', 48: 'GAA', 49: 'GAT', 50: 'GAC', 51: 'GAG', 52: 'GTA', 53: 'GTT', 54: 'GTC', 55: 'GTG', 56: 'GCA', 57: 'GCT', 58: 'GCC', 59: 'GCG', 60: 'GGA', 61: 'GGT', 62: 'GGC', 63: 'GGG'}


def execute_pipeline(p):
    p.execute()


def bits(f):
    return [(ord(s) >> i) & 1 for s in list(f) for i in xrange(7, -1, -1)]
    # for s in list(f):
    #     b = ord(s)
    #     for i in xrange(7, -1, -1):
    #         yield (b >> i) & 1


def min_lexo(k):
    if isinstance(k, str):
        k = Seq(k)
    l = [k, k.reverse_complement()]
    l.sort()
    return l[0]


class McDBG(object):

    def __init__(self, ports):
        # colour
        self.ports = ports
        self.sharding_level = int(math.log(len(ports), 4))
        assert len(ports) in [0, 4, 64]
        self.connections = {}
        self._create_connections()
        self.num_colours = self.get_num_colours()

    def _create_connections(self):
        # kmers stored in DB 2
        # colour arrays in DB 1
        # stats in DB 0
        self.connections['stats'] = {}
        self.connections['colours'] = {}
        self.connections['kmers'] = {}
        for i, port in enumerate(self.ports):
            self.connections['stats'][i] = redis.StrictRedis(
                host='localhost', port=port, db=0)
            # self.connections['colours'][i] = redis.StrictRedis(
            #     host='localhost', port=port, db=1)
            kmer_key = KMER_SHARDING[self.sharding_level][i]
            self.connections['kmers'][kmer_key] = redis.StrictRedis(
                host='localhost', port=port, db=2)

    def _create_kmer_pipeline(self, transaction=True):
        # kmers stored in DB 2
        # colour arrays in DB 1
        # stats in DB 0
        pipelines = {}
        for i, port in enumerate(self.ports):
            kmer_key = KMER_SHARDING[self.sharding_level][i]
            pipelines[kmer_key] = self.connections[
                'kmers'][kmer_key].pipeline(transaction=transaction)
        return pipelines

    def _execute_pipeline(self, pipelines):
        out = {}
        for kmer_key, p in pipelines.items():
            out[kmer_key] = p.execute()
        return out

    def set_kmer(self, kmer, colour):
        self.connections['kmers'][
            kmer[:self.sharding_level]].setbit(kmer, colour, 1)

    def set_kmers(self, kmers, colour):
        pipelines = self._create_kmer_pipeline(transaction=False)
        [pipelines[kmer[:self.sharding_level]].setbit(
            kmer, colour, 1) for kmer in kmers]
        self._execute_pipeline(pipelines)

    def _convert_query_kmers(self, kmers):
        return [k for k in [min_lexo(k) for k in kmers] if k[:self.sharding_level] in self.connections['kmers']]

    def query_kmers(self, kmers):
        kmers = self._convert_query_kmers(kmers)
        pipelines = self._create_kmer_pipeline()
        for kmer in kmers:
            pipelines[kmer[:self.sharding_level]].get(kmer)
        result = self._execute_pipeline(pipelines)
        out = [self._byte_arrays_to_bits(
            result[kmer[:self.sharding_level]].pop(0)) for kmer in kmers]
        return out

    def _create_bitop_lists(self):
        return dict((el, []) for el in self.connections['kmers'].keys())

    def query_kmers_100_per(self, kmers):
        kmers = self._convert_query_kmers(kmers)
        bit_op_lists = self._create_bitop_lists()
        for kmer in kmers:
            bit_op_lists[kmer[:self.sharding_level]].append(kmer)
        temporary_bitarrays = []
        for shard_key, kmers in bit_op_lists.items():
            if kmers:
                temporary_bitarrays.append(self._byte_arrays_to_bits(self.connections['kmers'][
                    shard_key].get('tmp')))
        return np.logical_and.reduce(temporary_bitarrays)
        # print(bit_op_lists)
        # r.bitop("AND",

    def query_kmers_old(self, kmers):
        pipelines = self._create_kmer_pipeline()
        num_colours = self.num_colours
        for kmer in kmers:
            for colour in range(num_colours):
                pipelines[kmer[:self.sharding_level]].getbit(kmer, colour)
        result = self._execute_pipeline(pipelines)
        outs = []
        for kmer in kmers:
            out = []
            for _ in range(num_colours):
                out.append(result[kmer[:self.sharding_level]].pop(0))
            outs.append(tuple(out))
        return outs

    def _byte_arrays_to_bits(self, _bytes):
        num_colours = self.num_colours
        tmp_v = [0]*(num_colours)
        if _bytes is not None:
            tmp_v = bits(_bytes)
        if len(tmp_v) < num_colours:
            tmp_v.extend([0]*(num_colours-len(tmp_v)))
        elif len(tmp_v) > num_colours:
            tmp_v = tmp_v[:num_colours]
            # [b for b in bits(_bytes)]
            # for i, bit in enumerate(bits(_bytes)):
            #     tmp_v[i] = bit
        return tuple(tmp_v)

    def kmers(self, N=-1, k='*'):
        i = 0
        # for connections in self.connections['kmers'].values():
        #     for kmer in connections.scan_iter(k):
        #         i += 1
        #         if (i > N and i > 0):
        #             break
        #         yield kmer
        for kmer in self.connections['kmers'][k[:3]].scan_iter(k):
            i += 1
            if (i > N and i > 0):
                break
            yield kmer

    def delete(self):
        for k, v in self.connections.items():
            for i, connection in v.items():
                connection.flushall()

    def add_sample(self, sample_name):
        existing_index = self.get_sample_colour(sample_name)
        if existing_index is not None:
            raise ValueError("%s already exists in the db" % sample_name)
        else:
            num_colours = self.sample_redis.get('num_colours')
            if num_colours is None:
                num_colours = 0
            else:
                num_colours = int(num_colours)
            pipe = self.sample_redis.pipeline()
            pipe.set('s%s' % sample_name, num_colours).incr('num_colours')
            pipe.execute()
            return num_colours
# >>> with r.pipeline() as pipe:
# ...     while 1:
# ...         try:
# ...             # put a WATCH on the key that holds our sequence value
# ...             pipe.watch('OUR-SEQUENCE-KEY')
# ...             # after WATCHing, the pipeline is put into immediate execution
# ...             # mode until we tell it to start buffering commands again.
# ...             # this allows us to get the current value of our sequence
# ...             current_value = pipe.get('OUR-SEQUENCE-KEY')
# ...             next_value = int(current_value) + 1
# ...             # now we can put the pipeline back into buffered mode with MULTI
# ...             pipe.multi()
# ...             pipe.set('OUR-SEQUENCE-KEY', next_value)
# ...             # and finally, execute the pipeline (the set command)
# ...             pipe.execute()
# ...             # if a WatchError wasn't raised during execution, everything
# ...             # we just did happened atomically.
# ...             break
# ...        except WatchError:
# ...             # another client must have changed 'OUR-SEQUENCE-KEY' between
# ...             # the time we started WATCHing it and the pipeline's execution.
# ...             # our best bet is to just retry.
# ...             continue

    def get_sample_colour(self, sample_name):
        return self.sample_redis.get('s%s' % sample_name)

    def colours_to_sample_dict(self):
        o = {}
        for s in self.sample_redis.keys('s*'):
            o[int(self.sample_redis.get(s))] = s[1:]
        return o

    @property
    def sample_redis(self):
        return self.connections['stats'][0]

    def get_num_colours(self):
        try:
            return int(self.sample_redis.get('num_colours'))
        except TypeError:
            return 0

    def count_kmers(self):
        return sum([r.dbsize() for r in self.connections['kmers'].values()])

    def calculate_memory(self):
        memory = sum([r.info().get('used_memory')
                      for r in self.connections['kmers'].values()])
        self.connections['stats'][1].set([self.count_kmers()], memory)
        return memory
