#!/usr/bin/env python3
import filecmp
import itertools
import json
import os
import sys
from collections import Counter
from collections import defaultdict
from datetime import timedelta
from timeit import default_timer as timer

from nm_tools import (get_exif_date, get_date_from_numbered_folder_path,
                      exists, join, dirname, basename, getsize)

duplicates_file_name = 'tmp/duplicates-by-size.json'
categorized_duplicates_file_name = 'tmp/duplicates-categorized.json'


def find_dupes_by_size():
    if not exists(duplicates_file_name):

        target_folder = sys.argv[1]
        if not target_folder:
            raise Exception("Define folder path")

        by_size = defaultdict(list)

        start = timer()
        for root, dirs, files in os.walk(target_folder):
            if '@eaDir' not in root:
                for file in files:
                    path = join(root, file)
                    assert exists(path), path+" not found"
                    size = getsize(path)
                    by_size[size].append(path)
                    if len(by_size) % 500 == 0:
                        print(timedelta(seconds=timer() - start),
                              ", amount of diff sizes: ", len(by_size))

        print("wasted time: ", timedelta(seconds=timer() - start))

        by_size_same_size = {k: v for k, v in by_size.items() if len(v) > 1}

        print("amount of sizes with duplicates:", len(by_size_same_size))
        with open(duplicates_file_name, 'w') as outfile:
            json.dump(by_size_same_size, outfile, indent=4)


def categorize_dupes():
    if exists(duplicates_file_name) \
            and not exists(categorized_duplicates_file_name):
        start = timer()
        with open(duplicates_file_name, 'r') as infile:
            by_size_same_size = json.load(infile)

            print("check equality of ", len(list(
                itertools.chain.from_iterable(by_size_same_size.values()))),
                  "files")
            out = defaultdict(dict)
            for _size, _paths1 in by_size_same_size.items():
                _paths1 = list(filter(exists, _paths1))
                for i, p1 in enumerate(_paths1[:-1]):
                    _paths2 = _paths1[i + 1:]
                    for p2 in _paths2:
                        if filecmp.cmp(p1, p2):
                            if i not in out[_size]:
                                out[_size][i] = set()
                            out[_size][i].add(p1)
                            out[_size][i].add(p2)
                            if _paths1 and p1 in _paths1:
                                _paths1.remove(p1)
                            if _paths1 and p2 in _paths1:
                                _paths1.remove(p2)

                            if len(out) % 10 == 0:
                                print("wasted time: ",
                                      timedelta(seconds=timer() - start),
                                      "count: ", len(out))

            # set(itertools.chain.from_iterable(out.values()))
            with open(categorized_duplicates_file_name, 'w') as outfile:
                def set_default(obj):
                    if isinstance(obj, set):
                        return list(obj)
                    raise TypeError

                json.dump(out, outfile, indent=4, default=set_default)


def clean_by_path_pattern(files, pos_pattern):
    existing_files = list(filter(exists, files))
    if len(existing_files) > 1:
        by_pattern = list(filter(lambda x: pos_pattern in x, existing_files))
        if by_pattern and len(by_pattern) < len(existing_files):
            print("remove", by_pattern, "from", files)
            os.remove(by_pattern[0])


def exif_date_equals_to_folder_date(f):
    exif = get_exif_date(f)
    if exif:
        from_folder = get_date_from_numbered_folder_path(f)
        if from_folder:
            from_folder_to_compare = from_folder\
                .replace(hour=0, minute=0,second=0)
            exif_to_compare = exif\
                .replace(hour=0, minute=0, second=0)

            return exif_to_compare == from_folder_to_compare
    return False


def clean_exif_folder_mismatches(files):
    files = list(filter(exists, files))
    if files and len(files) > 1:
        matches = {f: exif_date_equals_to_folder_date(f) for f in
                   files}
        if any(matches.values()):
            existing_mismatches = [f for f, m in matches.items() if not m]
            if existing_mismatches and len(existing_mismatches) < len(
                    files):
                for f in existing_mismatches:
                    print("remove", f, "from", files)
                    os.remove(f)
                    files.remove(f)
            else:
                print("ERROR: all file dupes matches file paths:",
                      files)
        else:
            print("ERROR: no file path matches exif:",
                  files)
    return files


def clean_in_unknown_folder(files):
    files = list(filter(exists, files))
    if files:
        file_in_unknown = list(
            filter(lambda x: basename(dirname(x)) == "unknown",
                   files))
        if file_in_unknown:
            print("remove", file_in_unknown, "from", files)
            while file_in_unknown and len(files) > 1:
                f = file_in_unknown.pop()
                files.remove(f)
                os.remove(f)
    return files


def clean_in_same_folder(files):
    files = list(filter(exists, files))
    if files:
        prefixes = Counter(map(dirname, files))
        excessive_prefixes = [k for k, v in prefixes.items() if v > 1]
        if excessive_prefixes:
            files_to_delete = list(sorted(
                filter(exists,
                       filter(
                           lambda x: dirname(x) in excessive_prefixes,
                           files))))
            if len(files_to_delete) > 1:
                files_to_delete_x = files_to_delete[: -1]
                print("remove", files_to_delete_x, "from", files_to_delete)
                for f in files_to_delete_x:
                    os.remove(f)
                    files.remove(f)
    return files


def clean_dupes():
    if exists(categorized_duplicates_file_name):
        with open(categorized_duplicates_file_name, 'r') as infile2:
            print("remove files from", categorized_duplicates_file_name)
            dups = json.load(infile2)
            for index, v in enumerate(dups.values()):
                for files in v.values():
                    files2 = clean_in_same_folder(files)
                    files3 = clean_in_unknown_folder(files2)
                    files4 = clean_exif_folder_mismatches(files3)
                    assert files4, "at least one file should exist after clean"
                    # clean_by_path_pattern(v2, "byYears/2019/04/23/")


if __name__ == '__main__':
    find_dupes_by_size()
    categorize_dupes()
    clean_dupes()
