#!/usr/bin/env python3
import filecmp
import itertools
import json
import os
import sys
from collections import defaultdict
from datetime import timedelta
from timeit import default_timer as timer
duplicates_file_name = 'duplicates1.json'
categorized_duplicates_file_name = 'duplicates-categorized.json'
if not os.path.exists(duplicates_file_name):

    target_folder = sys.argv[1]
    if not target_folder:
        raise Exception("Define folder path")

    by_size = defaultdict(list)

    start = timer()
    for root, dirs, files in os.walk(target_folder):
        if '@eaDir' not in root:
            for file in files:
                path = os.path.join(root, file)
                size = os.path.getsize(path)
                by_size[size].append(path)
                if len(by_size) % 500 == 0:
                    print(timedelta(seconds=timer() - start), ", amount of diff sizes: ", len(by_size))

    print("wasted time: ", timedelta(seconds=timer() - start))

    by_size_same_size = {k: v for k, v in by_size.items() if len(v) > 1}

    print("amount of sizes with duplicates:", len(by_size_same_size))
    with open(duplicates_file_name, 'w') as outfile:
        json.dump(by_size_same_size, outfile, indent=4)

start = timer()
with open(duplicates_file_name, 'r') as infile:
    by_size_same_size = json.load(infile)

    print("check equality of ", len(list(itertools.chain.from_iterable(by_size_same_size.values()))), "files")
    out = defaultdict(dict)
    for _size, _paths in by_size_same_size.items():
        for i, p1 in enumerate(_paths[:-1]):
            for p2 in _paths[i + 1:]:
                if _size in out:
                    found_duplicates = set(itertools.chain.from_iterable(out[_size].values()))
                    if p1 in found_duplicates and p1 in _paths:
                        _paths.remove(p1)
                        continue
                    if p2 in found_duplicates and p2 in _paths:
                        _paths.remove(p2)
                        continue
                if filecmp.cmp(p1, p2):
                    if i not in out[_size]:
                        out[_size][i] = list()
                    out[_size][i].append(p1)
                    out[_size][i].append(p2)
                    if len(out) % 10 == 0:
                        print("wasted time: ", timedelta(seconds=timer() - start), "count: ", len(out))

    # set(itertools.chain.from_iterable(out.values()))
    with open(categorized_duplicates_file_name, 'w') as outfile:
        json.dump(out, outfile, indent=4)
