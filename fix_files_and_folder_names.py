#!/usr/bin/env python3
import os
import sys
from nm_tools import *
from os.path import join
from unidecode import unidecode




def process_name(name):
    n_name = re.sub(r"\s+", "_", name)
    n_n_name = unidecode(n_name)
    n_n_n_name = re.sub(r"(\W)\1+", r"\1", n_n_name)
    n_n_n_n_name = re.sub("_-_", "_",      n_n_n_name)
    n_n_n_n_n_name = re.sub(r"_g\.$", "",  n_n_n_n_name)
    n_n_n_n_n_n_name = n_n_n_n_n_name\
        .replace("'", "").replace('"', "")\
        .replace("(", "").replace(")", "")\
        .replace("?", "")

    out = n_n_n_n_n_n_name
    return out


def rename_loop(l):
    for index, old_e in enumerate(l):
        new_e = process_name(old_e)
        if new_e != old_e:
            old_full_e = join(root, old_e)
            new_full_e = join(root, new_e)
            os.rename(old_full_e, new_full_e)
            print(old_e, " -> ", new_e)
            l[index] = new_e


if __name__ == "__main__":
    target_folder = sys.argv[1]
    if not target_folder:
        raise Exception("Define folder path")
    for root, dirs, files in os.walk(target_folder):
        if '@eaDir' not in root:
            rename_loop(dirs)
            rename_loop(files)
