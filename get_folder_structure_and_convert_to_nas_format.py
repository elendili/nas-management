#!/usr/bin/env python3
"""Merge remote photo directories into folder
with date-based folder structure: yyyy/MM/dd/<file>
Script uses EXIF and input folder structure to get photo date
and update access/modification file date by photo date.
Script checks if destination has duplicate by size/content
and name started from original file name.
Script updates file access/modification date from
"""
import atexit
import os
import sys
from pathlib import Path

import spur
import yaml

from nm_tools import *

timings = []

def migrate_file_if_no_duplicate(local_input_folder,
                                 input_path, new_root, file, file_datetime):
    output_path = join(new_root, file)
    if remote_exists(output_path):
        globbed_file = re.sub(r"(\.\w+$)", r"*\1", file)
        globbed_path = join(new_root, globbed_file)
        globbed_paths = glob.glob(globbed_path)
        for gp in globbed_paths:
            if are_equal(input_path, gp):
                logging.info("Skip %s because total duplicate exists in output"
                             % Path(input_path).relative_to(local_input_folder))
                break

        else:
            new_file = add_suffix_to_file(file, file_datetime)
            output_path = join(new_root, new_file)
            migrate_file(input_path, output_path)
    else:
        migrate_file(input_path, output_path)


def migrate_file(src_path, new_path):
    assert not remote_exists(new_path), "file should not exist: " + new_path
    os.makedirs(dirname(new_path), exist_ok=True)
    input_file = src_path.replace(local_root, remote_root)
    output_file = new_path.replace(local_root, remote_root)
    logging.info("Link %s to %s" % (input_file, output_file))
    try:
        shell.run(["cp", "-lnp", input_file, output_file])
    except Exception as e:
        on_error(e)


def remote_file_size(file):
    try:
        return os.stat(file).st_size
    except:
        remote_file = file.replace(local_root, remote_root)
        result = shell.run(["stat", "-c", "%s", remote_file])
        out = int(result.output)
        return out


def remote_exists(file):
    try:
        out = Path(file).exists()
    except:
        remote_file = file.replace(local_root, remote_root)
        result = shell.run(["test", "-e", remote_file], allow_error=True)
        out = result.return_code == 0
    return out


def are_equal(f1, f2):
    f1, f2 = map(str, (f1, f2))
    size1 = remote_file_size(f1)
    size2 = remote_file_size(f2)
    if size1 == size2:
        out = are_files_equal_by_content(f1, f2)
        return out
    else:
        return False


def process_file(root, file, local_input_folder, local_output_folder):
    input_path = join(root, file)
    file_datetime = get_file_datetime(input_path)
    # rename out file
    new_file = re.sub(r"[()]+", "", file)
    new_file = re.sub(r"\s+", "_", new_file)
    if file_datetime:
        epoch_time = file_datetime.timestamp()
        logging.info("update time of %s to %s " %
                     (Path(input_path).relative_to(local_input_folder),
                      file_datetime))

        # update modification name
        os.utime(input_path, (epoch_time, epoch_time))

        new_root = join(local_output_folder,
                        "%04d" % file_datetime.year,
                        "%02d" % file_datetime.month,
                        "%02d" % file_datetime.day)
        os.makedirs(new_root, exist_ok=True)
        migrate_file_if_no_duplicate(local_input_folder,
                                     input_path, new_root,
                                     new_file, file_datetime)
    else:
        new_root = join(local_output_folder, "unknown")
        logging.warning("File has no date info " + input_path)
        migrate_file_if_no_duplicate(local_input_folder,
                                     input_path, new_root,
                                     new_file, file_datetime)


def process_folder(local_input_folder,
                   local_output_folder,
                   filter_by_filename_regex):
    os.makedirs(local_output_folder, exist_ok=True)
    for root, dirs, files in os.walk(local_input_folder, onerror=on_error):
        if '@eaDir' not in root:
            for file in files:
                file_path = join(root, file)
                if not file.startswith("."):
                    if re.fullmatch(filter_by_filename_regex, file):
                        process_file(root, file,
                                     local_input_folder,
                                     local_output_folder)
                    else:
                        print("File '%s' was ignored, "
                              "because doesn't match pattern %s."
                              % (file_path, filter_by_filename_regex))
                else:
                    print("File '%s' was ignored, "
                          "because starts with ."
                          % file_path)


def prepare_logging():
    log_folder = join(os.getcwd(), "logs/")
    os.makedirs(log_folder, exist_ok=True)
    log_file_name = re.sub(r"\D", "", str(datetime.datetime.now())) + '.log'
    log_file_path = join(log_folder, log_file_name)
    logging.basicConfig(filename=log_file_path,
                        level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


def on_error(error):
    logging.error(error)
    raise error


def exit_f():
    if timings:
        print("Timings sum:", sum(timings))
        print("Average time:", sum(timings) / len(timings))
    print("Total time:", current_milli_time() - start_execution_time)


start_execution_time = current_milli_time()

if __name__ == "__main__":
    prepare_logging()
    atexit.register(exit_f)
    assert len(sys.argv) > 1, "define path to arguments file"
    arg_file = sys.argv[1]
    logging.info("Arg file: " + arg_file)
    with open(arg_file) as json_file:
        data = yaml.safe_load(json_file)
        local_root = data["local_root"]
        remote_root = data["remote_root"]
        output_folder = data["output_folder"]
        filter_by_filename_regex = data["filter_by_filename_regex"]
        connection_data = data["ssh-connection-data"]

    with spur.SshShell(**connection_data) as shell:
        for input_folder in data["input_folders"]:
            _local_input_folder = join(local_root, input_folder)
            assert remote_exists(_local_input_folder), \
                "input folder " + _local_input_folder + " not exist"
            _local_output_folder = join(local_root, output_folder)
            process_folder(_local_input_folder,
                           _local_output_folder,
                           filter_by_filename_regex)