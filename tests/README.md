# Running tests
## Overview
This directory contains two python files for the Tests, a testdata set and a script to generate and ingest the testdata set. You should run tests from the root-directory of this git repository.

# Setting up the environment
Please modify `test_es2json_esfunctions.py` on Line 6 and 7 and `init_testdata.sh` on line 4 if your elasticsearch instance isn't running on localhost:9200. The testdata can be self-generated by using `generate_testdata.py`.

`init_testdata.sh` uses [esbulk](https://github.com/miku/esbulk) for indexing the testdata.

# Running the tests
simply run `python3 -m pytest tests/` from the root directory of this git repository.