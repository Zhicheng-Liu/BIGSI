from remcdbg.mcdbg import McDBG
from remcdbg.utils import kmer_to_bits
import random
ports = [6200, 6201, 6202, 6203]
KMERS = ['A', 'T', 'C', 'G']


def test_add_kmer():
    mc = McDBG(ports=ports, compress_kmers=True)
    kmer = 'AGAGATATAGACTTATTAAAAAATACAATAT'
    bitstring = kmer_to_bits(kmer)
    # print(bitstring)
    # print([mc.connections['kmers']['A'].setbit('tmp', int(i), int(j))
    # for i, j in enumerate(bitstring)])
    # print(mc.connections['kmers']['A'].get('tmp'))
    # mc._kmer_to_bytes()
    mc.set_kmer('AGAGATATAGACTTATTAAAAAATACAATAT', 1)
    _bytes = b'6\xc8\xcd\xb23l\x8c\xd8'
    # print(mc.connections['kmers']['A'].getbit(
    # _bytes, 1))
    assert mc.connections['kmers']['A'].getbit(
        _bytes, 1) == 1
    assert mc.connections['kmers']['T'].getbit(
        _bytes, 1) == 0
    mc.delete()
    assert mc.connections['kmers']['A'].getbit(
        _bytes, 1) == 0
    assert mc.connections['kmers']['T'].getbit(
        _bytes, 1) == 0


def test_add_kmers():
    mc = McDBG(ports=ports, compress_kmers=True)
    mc.set_kmers(
        ['ATCGTAGATATCGTAGATATCGTAGATATCG', 'AGATATTGTAGATATTGTAGATATTGTAGAT'], 1)
    _bytes = b'#>\xc8\xcf\xb23\xec\x8c'
    _bytes2 = b'6\xc8\xcd\xb23l\x8c\xd8'
    assert mc.connections['kmers']['A'].getbit(
        _bytes, 1) == 1
    assert mc.connections['kmers']['A'].getbit(
        _bytes2, 1) == 1
    assert mc.connections['kmers']['C'].getbit(
        _bytes, 1) == 0
    assert mc.connections['kmers']['C'].getbit(
        _bytes2, 1) == 0
    mc.delete()


def test_query_kmers():
    mc = McDBG(ports=ports, compress_kmers=True)
    mc.delete()

    mc.add_sample('1234')
    mc.add_sample('1235')
    mc.add_sample('1236')

    mc.set_kmers(
        ['ATCGTAGATATCGTAGATATCGTAGATATCG', 'ATCTACAATATCTACAATATCTACAATATCT'], 0)
    mc.set_kmers(
        ['ATCGTAGATATCGTAGATATCGTAGATATCG', 'ATTGTAGAGATTGTAGAGATTGTAGAGATTA'], 1)
    mc.set_kmers(
        ['ATCGTAGACATCGTAGACATCGTAGACATCG', 'ATTGTAGAGATTGTAGAGATTGTAGAGATTA'], 2)
    assert mc.get_num_colours() == 3
    mc.num_colours = mc.get_num_colours()
    assert mc.query_kmers(['ATCGTAGATATCGTAGATATCGTAGATATCG', 'ATCTACAATATCTACAATATCTACAATATCT']) == [
        (1, 1, 0), (1, 0, 0)]
    mc.delete()

    mc.add_sample('1234')
    mc.add_sample('1235')
    mc.add_sample('1236')

    mc.set_kmers(
        ['ATCGTAGATATCGTAGATATCGTAGATATCG', 'CTTGTAGATCTTGTAGATCTTGTAGATCTTG'], 0)
    mc.set_kmers(
        ['ATCGTAGATATCGTAGATATCGTAGATATCG', 'ATTGTAGAGATTGTAGAGATTGTAGAGATTA'], 1)
    mc.set_kmers(
        ['ATCGTAGACATCGTAGACATCGTAGACATCG', 'ATTGTAGAGATTGTAGAGATTGTAGAGATTA'], 2)
    assert mc.query_kmers(['ATCGTAGATATCGTAGATATCGTAGATATCG', 'CTTGTAGATCTTGTAGATCTTGTAGATCTTG']) == [
        (1, 1, 0), (1, 0, 0)]
