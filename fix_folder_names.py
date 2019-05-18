#!/usr/bin/env python3
# preocess results of
# find . ! -empty -type f -exec md5sum {} + | sort | uniq -w32 -dD | tee ../logdupes
import os
import re
import sys

from unidecode import unidecode

target_folder = sys.argv[1]
if not target_folder:
    raise Exception("Define folder path")


def process_name(name):
    n_name = re.sub(r"\s+", "_", name)
    n_n_name = unidecode(n_name)
    n_n_n_name = re.sub(r"(\W)\1+", r"\1", n_n_name)
    n_n_n_n_name = re.sub("_-_", "_", n_n_n_name)
    n_n_n_n_n_name = re.sub(r"_g\.$", "", n_n_n_n_name)
    return n_n_n_n_n_name


def rename(root, e):
    old_d = os.path.join(root, e)
    new_e = process_name(e)
    new_d = os.path.join(root, new_e)
    os.rename(old_d, new_d)
    print(e, " -> ", new_e)


for root, dirs, files in os.walk(target_folder):
    if '@eaDir' not in root:
        for d in dirs:
            rename(root, d)
        for f in files:
            rename(root, f)
