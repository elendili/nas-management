#!/usr/bin/env python3
"""Merge remote photo directories into folder
with date-based folder structure: yyyy/MM/dd/<file>
Script uses EXIF and input folder structure to get photo date
and update access/modification file date by photo date.
Script checks if destination has duplicate by size/content
and name started from original file name.
Script updates file access/modification date from
"""
import glob
import json
import logging
import sys
import os
from pathlib import Path

import spur

from nm_tools import *

connection_data = {"hostname": "192.168.1.36", "username": "elendili",
                   "private_key_file": "/Users/elendili/.ssh/id_rsa"}


def get_file_datetime(file_path):
    exif_date = get_exif_date(file_path)
    folder_date = get_date_from_folder_path(file_path)
    if exif_date:
        return exif_date
    elif folder_date:
        return folder_date
    else:
        logging.error("No exif or folder date to extract for " + file_path)
    pass


def migrate_file(src_path, new_path):
    os.makedirs(os.path.dirname(new_path), exist_ok=True)
    input_file = src_path.replace(local_root, remote_root)
    output_file = new_path.replace(local_root, remote_root)
    logging.info("Link %s to %s" % (input_file, output_file))
    try:
        shell.run(["cp", "-lp", input_file, output_file])
    except Exception as e:
        raise e


def exists(file):
    remote_file = file.replace(local_root, remote_root)
    result = shell.run(["test", "-e", remote_file], allow_error=True)
    out = result.return_code == 0
    return out


def are_equal(f1, f2):
    return os.path.getsize(f1) == os.path.getsize(f2) \
           and compare_files(f1, f2)


def process_file(root, file):
    input_path = os.path.join(root, file)
    file_datetime = get_file_datetime(input_path)
    if file_datetime:
        epoch_time = file_datetime.timestamp()
        logging.info("update time of %s to %s " %
                     (Path(input_path).relative_to(local_input_folder), file_datetime))
        os.utime(input_path, (epoch_time, epoch_time))

        new_root = os.path.join(local_output_folder,
                                "%04d" % file_datetime.year,
                                "%02d" % file_datetime.month,
                                "%02d" % file_datetime.day)
        os.makedirs(new_root, exist_ok=True)
        output_path = os.path.join(new_root, file)
        if exists(output_path):
            globbed_file = re.sub(r"(\.\w+$)", r"*\1", file)
            globbed_path = os.path.join(new_root, globbed_file)
            globbed_paths = glob.glob(globbed_path)
            for gp in globbed_paths:
                if are_equal(input_path, gp):
                    logging.info("Skip %s because total duplicate exists in output"
                                 % Path(input_path).relative_to(local_input_folder))
                    break
            else:
                new_file = add_suffix_to_file(file, file_datetime)
                output_path = os.path.join(new_root, new_file)
                migrate_file(input_path, output_path)
        else:
            migrate_file(input_path, output_path)
    else:
        logging.warning("File has no date info " + input_path)
        output_path = os.path.join(local_output_folder, "unknown", file)
        if exists(output_path):
            new_file = add_suffix_to_file(file, file_datetime)
            output_path = os.path.join(local_output_folder, "unknown", new_file)
        migrate_file(input_path, output_path)
    # exit(1)


def process_folder():
    for root, dirs, files in os.walk(local_input_folder):
        if '@eaDir' not in root:
            for file in files:
                if not file.startswith("."):
                    process_file(root, file)


def prepare_logging():
    log_folder = os.path.join(os.getcwd(), "logs/")
    os.makedirs(log_folder, exist_ok=True)
    log_file_name = re.sub(r"\D", "", str(datetime.datetime.now())) + '.log'
    log_file_path = os.path.join(log_folder, log_file_name)
    logging.basicConfig(filename=log_file_path,
                        level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


if __name__ == "__main__":
    prepare_logging()
    assert len(sys.argv) > 1, "define path to arguments file"
    arg_file = sys.argv[1]
    logging.info("Arg file: " + arg_file)
    with spur.SshShell(**connection_data) as shell:
        with open(arg_file) as json_file:
            data = json.load(json_file)
            local_root = data["local_root"]
            remote_root = data["remote_root"]
            output_folder = data["output_folder"]
            for input_folder in data["input_folders"]:
                local_input_folder = os.path.join(local_root, input_folder)
                assert exists(local_input_folder), "input folder " + local_input_folder + " not exist"
                local_output_folder = os.path.join(local_root, output_folder)
                remote_input_folder = os.path.join(remote_root, input_folder)
                remote_output_folder = os.path.join(remote_root, output_folder)
                os.makedirs(local_output_folder, exist_ok=True)
                process_folder()
