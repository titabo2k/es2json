import es2json
import json
import uuid
import os
import gzip
from copy import deepcopy
from generate_testdata import MAX


default_kwargs = {
    "host": "localhost",
    "port": 9200,
    "index": "test",
    "type": "_doc",
}


default_returnrecord = {"_index": "test",
                        "_score": None,
                        "_type": "_doc",
                        "_source": {}
                        }


testdata = []
with gzip.open("tests/testdata.ldj.gz", "rt") as inp:
    for line in inp:
        testdata.append(json.loads(line))


def call_object(object, use_with=False, **kwargs):
    if use_with:
        with object(**kwargs) as es:
            for record in es.generator():
                yield record
    else:
        es = object(**kwargs)
        for record in es.generator():
            yield record


def test_esgenerator(**kwargs):
    expected_records = []
    for n, record in enumerate(testdata):
        retrecord = deepcopy(default_returnrecord)
        retrecord["_source"] = record
        retrecord["_id"] = str(n)
        expected_records.append(dict(sorted(retrecord.items())))
    for boolean in (True, False):
        records = []
        for n, record in enumerate(call_object(es2json.ESGenerator, use_with=boolean, **default_kwargs, **kwargs)):
            record.pop("sort")  # different behaviour between es6 and es7 and tbh, we don't care about the sort parameter in this test
            records.append(dict(sorted(record.items())))
        assert sorted(expected_records, key=lambda k: k["_id"]) == sorted(records, key=lambda k: k["_id"])


def test_esgenerator_NoneSource():
    expected_records = []
    for n, record in enumerate(testdata):
        retrecord = deepcopy(default_returnrecord)
        retrecord["_id"] = str(n)
        expected_records.append(dict(sorted(retrecord.items())))
    for boolean in (True, False):
        records = []
        for n, record in enumerate(call_object(es2json.ESGenerator, use_with=boolean, source=False, **default_kwargs)):
            record.pop("sort")  # different behaviour between es6 and es7 and tbh, we don't care about the sort parameter in this test
            records.append(dict(sorted(record.items())))
        assert sorted(expected_records, key=lambda k: k["_id"]) == sorted(records, key=lambda k: k["_id"])


def test_esgenerator_source_includes():
    includes = ["foo"]
    expected_records = []
    for n, record in enumerate(testdata):
        retrecord = deepcopy(default_returnrecord)
        for item in includes:
            retrecord["_source"][item] = record[item]
        retrecord["_id"] = str(n)
        expected_records.append(dict(sorted(retrecord.items())))
    for boolean in (True, False):
        records = []
        for record in call_object(es2json.ESGenerator, use_with=boolean, includes=includes, **default_kwargs):
            record.pop("sort")  # different behaviour between es6 and es7 and tbh, we don't care about the sort parameter in this test
            records.append(dict(sorted(record.items())))
        assert sorted(expected_records, key=lambda k: k["_id"]) == sorted(records, key=lambda k: k["_id"])


def test_esgenerator_source_excludes():
    expected_records = []
    for n in range(0, MAX):
        retrecord = deepcopy(default_returnrecord)
        retrecord["_id"] = str(n)
        retrecord["_source"]["foo"] = n
        retrecord["_source"]["baz"] = "test{}".format(n)
        expected_records.append(dict(sorted(retrecord.items())))
    for boolean in (True, False):
        records = []
        for record in call_object(es2json.ESGenerator, use_with=boolean, excludes="bar", **default_kwargs):
            record.pop("sort")  # different behaviour between es6 and es7 and tbh, we don't care about the sort parameter in this test
            records.append(dict(sorted(record.items())))
        assert sorted(expected_records, key=lambda k: k["_id"]) == sorted(records, key=lambda k: k["_id"])


def test_esgenerator_query_headless():
    query = {"query": {"match": {"baz.keyword": "test666"}}}
    enter = False
    for boolean in (True, False):
        records = []
        for record in call_object(es2json.ESGenerator, use_with=boolean, body=query, headless=True, **default_kwargs):
            enter = True
            assert record == {"foo": 666, "bar": MAX-666, "baz": "test666"}
        assert enter  # testing if we even entered the generator() at all...useful for tests where we assert directly when iterating over the generator

def test_esidfilegenerator_iterable():
    expected_records = []
    ids = []
    for n in range(200, 300):
        retrecord = {}
        retrecord["foo"] = n
        retrecord["baz"] = "test{}".format(n)
        retrecord["bar"] = MAX-n
        expected_records.append(dict(sorted(retrecord.items())))
        ids.append(str(n))
    for boolean in (True, False):
        records = []
        for record in call_object(es2json.IDFile, use_with=boolean, idfile=ids, headless=True, **default_kwargs):
            records.append(dict(sorted(record.items())))
        assert sorted(expected_records, key=lambda k: k["foo"]) == sorted(records, key=lambda k: k["foo"])


def test_esidfilegenerator_file():
    fd = str(uuid.uuid4())
    expected_records = []
    with open(fd, "w") as outp:
        for n in range(200, 300):
            retrecord = {}
            retrecord["foo"] = n
            retrecord["baz"] = "test{}".format(n)
            retrecord["bar"] = MAX-n
            expected_records.append(dict(sorted(retrecord.items())))
            print(n, file=outp)
    for boolean in (True, False):
        records = []
        for record in call_object(es2json.IDFile, use_with=boolean, idfile=fd, headless=True, **default_kwargs):
            records.append(dict(sorted(record.items())))
        assert sorted(expected_records, key=lambda k: k["foo"]) == sorted(records, key=lambda k: k["foo"])
    os.remove(fd)


def test_eidfileconsumegenerator():
    fd = str(uuid.uuid4())
    for boolean in (True, False):
        expected_records = []
        with open(fd, "w") as outp:
            for n in range(MAX-200, MAX-100):
                retrecord = {}
                retrecord["foo"] = n
                retrecord["baz"] = "test{}".format(n)
                retrecord["bar"] = MAX-n
                expected_records.append(dict(sorted(retrecord.items())))
                print(n, file=outp)
        records = []
        for record in call_object(es2json.IDFileConsume, use_with=boolean, idfile=fd, headless=True, **default_kwargs):
            records.append(dict(sorted(record.items())))
        assert sorted(expected_records, key=lambda k: k["foo"]) == sorted(records, key=lambda k: k["foo"])
        assert es2json.isfile(fd) is False


def test_eidfileconsumegenerator_query():
    fd = str(uuid.uuid4())
    for boolean in (True, False):
        expected_records = []
        with open(fd, "w") as outp:
            for n in range(MAX-200, MAX-100):
                if str(n).startswith('9'):
                    retrecord = {}
                    retrecord["foo"] = n
                    retrecord["baz"] = "test{}".format(n)
                    retrecord["bar"] = MAX-n
                    expected_records.append(dict(sorted(retrecord.items())))
                    print(n, file=outp)
        query = {"query": {"prefix":  {"baz": "test9"}}}
        records = []
        for record in call_object(es2json.IDFileConsume, use_with=boolean, idfile=fd, headless=True, body=query, **default_kwargs):
            records.append(dict(sorted(record.items())))
        assert sorted(expected_records, key=lambda k: k["foo"]) == sorted(records, key=lambda k: k["foo"])
        assert es2json.isfile(fd) is False


def test_eidfileconsumegenerator_missing_ids():
    fd = str(uuid.uuid4())
    for boolean in (True, False):
        expected_records = []
        found_ids = set()
        with open(fd, "w") as outp:
            for n in range(MAX-100, MAX+200):
                print(n, file=outp)
                if n < MAX:
                    retrecord = {}
                    retrecord["foo"] = n
                    retrecord["baz"] = "test{}".format(n)
                    retrecord["bar"] = MAX-n
                    expected_records.append(dict(sorted(retrecord.items())))
        records = []
        enter = False
        for record in call_object(es2json.IDFileConsume, use_with=boolean, idfile=fd, headless=False, **default_kwargs):
            enter = True
            found_ids.add(record["_id"])
            assert dict(sorted(record["_source"].items())) in expected_records
        assert enter
        with open(fd, "r") as inp:
            for ppn in inp:
                assert ppn.rstrip() not in found_ids
        os.remove(fd)  # cleanup


def test_eidfileconsumegenerator_missing_ids_query():
    fd = str(uuid.uuid4())
    for boolean in (True, False):
        expected_records = []
        found_ids = set()
        with open(fd, "w") as outp:
            for n in range(MAX-200, MAX+200):
                print(n, file=outp)
                if n < MAX and str(n).startswith("9"):
                    retrecord = {}
                    retrecord["foo"] = n
                    retrecord["baz"] = "test{}".format(n)
                    retrecord["bar"] = MAX-n
                    expected_records.append(dict(sorted(retrecord.items())))
        query = {"query": {"prefix":  {"baz": "test9"}}}
        records = []
        enter = False
        for record in call_object(es2json.IDFileConsume, use_with=boolean, idfile=fd, headless=False, **default_kwargs):
            enter = True
            found_ids.add(record["_id"])
            assert dict(sorted(record["_source"].items())) in expected_records
        assert enter
        with open(fd, "r") as inp:
            for ppn in inp:
                assert ppn.rstrip() not in found_ids
        os.remove(fd)  # cleanup


def test_esfatgenerator():
    expected_records = []
    for n in range(0, MAX):
        retrecord = deepcopy(default_returnrecord)
        retrecord["_id"] = str(n)
        retrecord["_source"]["foo"] = n
        retrecord["_source"]["bar"] = MAX-n
        retrecord["_source"]["baz"] = "test{}".format(n)
        expected_records.append(dict(sorted(retrecord.items())))
    records = []
    for fatrecords in es2json.esfatgenerator(**default_kwargs):
        for record in fatrecords:
            record.pop("sort")
            records.append(dict(sorted(record.items())))
    assert sorted(expected_records, key=lambda k: k["_id"]) == sorted(records, key=lambda k: k["_id"])
