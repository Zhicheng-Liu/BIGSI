from bigsi.storage import RedisStorage
from bigsi.storage import BerkeleyDBStorage
from bigsi.storage import RocksDBStorage
from bigsi.matrix import BitMatrix
from bigsi.bloom import BloomFilter
from bigsi.graph.index import KmerSignatureIndex
from bitarray import bitarray
import pytest
from bigsi.utils import convert_query_kmers


def get_storages():
    return [RedisStorage(), BerkeleyDBStorage(), RocksDBStorage()]


def test_lookup1():
    bloomfilter_size = 250
    number_hash_functions = 3
    kmers1 = ["ATC", "ATG", "ATA", "ATT"]
    kmers2 = ["ATC", "ATG", "ATA", "TTT"]
    bloomfilter1 = BloomFilter(bloomfilter_size, number_hash_functions).update(
        convert_query_kmers(kmers1)
    )  # canonical
    bloomfilter2 = BloomFilter(bloomfilter_size, number_hash_functions).update(
        convert_query_kmers(kmers2)
    )
    bloomfilters = [bloomfilter1.bitarray, bloomfilter2.bitarray]
    for storage in get_storages():
        storage.delete_all()

        KmerSignatureIndex.create(
            storage, bloomfilters, bloomfilter_size, number_hash_functions
        )
        ksi = KmerSignatureIndex(storage)

        assert ksi.lookup(["ATC"]) == {"ATC": bitarray("11")}
        print(ksi.lookup(["ATC", "ATC", "ATT"]))
        assert ksi.lookup(["ATC", "ATC", "ATT"]) == {
            "ATC": bitarray("11"),
            "ATT": bitarray("10"),
        }
        assert ksi.lookup(["ATC", "ATC", "ATT", "TTT"]) == {
            "ATC": bitarray("11"),
            "ATT": bitarray("10"),
            "TTT": bitarray("01"),
        }


def test_lookup2():
    bloomfilter_size = 2500
    number_hash_functions = 2
    kmers1 = ["ATC", "ATG", "ATA", "ATT"]
    kmers2 = ["ATC", "ATG", "ATA", "TTT"]
    bloomfilter1 = BloomFilter(bloomfilter_size, number_hash_functions).update(
        convert_query_kmers(kmers1)
    )
    bloomfilter2 = BloomFilter(bloomfilter_size, number_hash_functions).update(
        convert_query_kmers(kmers2)
    )
    bloomfilters = [bloomfilter1, bloomfilter2]
    for storage in get_storages():
        storage.delete_all()

        ksi = KmerSignatureIndex.create(
            storage, bloomfilters, bloomfilter_size, number_hash_functions
        )

        assert ksi.lookup(["ATC"]) == {"ATC": bitarray("11")}
        assert ksi.lookup(["ATC", "ATC", "ATT"]) == {
            "ATC": bitarray("11"),
            "ATT": bitarray("10"),
        }
        assert ksi.lookup(["ATC", "ATC", "ATT", "TTT"]) == {
            "ATC": bitarray("11"),
            "ATT": bitarray("10"),
            "TTT": bitarray("01"),
        }


def test_lookup3():
    bloomfilter_size = 250
    number_hash_functions = 1
    kmers1 = ["ATC", "ATG", "ATA", "ATT"]
    kmers2 = ["ATC", "ATG", "ATA", "TTT"]
    bloomfilter1 = BloomFilter(bloomfilter_size, number_hash_functions).update(
        convert_query_kmers(kmers1)
    )
    bloomfilter2 = BloomFilter(bloomfilter_size, number_hash_functions).update(
        convert_query_kmers(kmers2)
    )
    bloomfilters = [bloomfilter1, bloomfilter2]
    for storage in get_storages():
        storage.delete_all()
        ksi = KmerSignatureIndex.create(
            storage, bloomfilters, bloomfilter_size, number_hash_functions
        )

        assert ksi.lookup(["ATC"]) == {"ATC": bitarray("11")}
        assert ksi.lookup(["ATC", "ATC", "ATT"]) == {
            "ATC": bitarray("11"),
            "ATT": bitarray("10"),
        }
        assert ksi.lookup(["ATC", "ATC", "ATT", "TTT"]) == {
            "ATC": bitarray("11"),
            "ATT": bitarray("10"),
            "TTT": bitarray("01"),
        }
