import datetime
import filecmp
import hashlib
import logging
import os
import re
import time

import PIL.ExifTags
import PIL.Image


def get_md5(file):
    file = str(file)
    hash_md5 = hashlib.md5()
    with open(file, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def are_files_equal_by_content(filename1, filename2):
    out = filecmp.cmp(filename1, filename2)
    return out


def get_file_modification_date(file_path):
    mtime = os.path.getmtime(file_path)
    out = datetime.datetime.fromtimestamp(mtime)
    period = out - datetime.datetime.now()
    if abs(period.days) > 365:
        return out
    else:
        return None


def get_file_datetime(file_path):
    exif_date = get_exif_date(file_path)
    file_modification_date = get_file_modification_date(file_path)
    folder_date = get_date_from_folder_path(file_path)
    if exif_date:
        return exif_date
    if file_modification_date:
        return file_modification_date
    elif folder_date:
        return folder_date
    else:
        logging.error("No exif or folder date to extract for " + file_path)


def get_date_from_folder_path(file_path):
    file_path = str(file_path)
    found1 = re.search(r"\D\d{2}(\D)\d{2}\1{1}20\d{2}\1", file_path)
    found2 = re.search(r"\D20\d{2}\D\d{2}\D\d{2}\D", file_path)
    if found1:
        s = filter(None, re.split(r"\D+", found1.group(0)))
        f_day, f_month, f_year = map(int, s)
    elif found2:
        s = filter(None, re.split(r"\D+", found2.group(0)))
        f_year, f_month, f_day = map(int, s)
    else:
        return None
    if f_month > 12:
        f_month, f_day = f_day, f_month
    try:
        out = datetime.datetime(year=f_year, month=f_month, day=f_day)
        return out
    except Exception as e:
        logging.error("Error on extracting date from " + file_path, exc_info=e)
        raise e


def get_exif_date(file_path):
    file_path = str(file_path)
    if not file_path.endswith(".MOV") and not file_path.endswith(".PNG"):
        try:
            img = PIL.Image.open(file_path)
            exif_dict = img._getexif()
        except Exception as e:
            print(file_path, e, sep="\n")
            return None
        if exif_dict is not None:
            exif = {
                PIL.ExifTags.TAGS[k]: v
                for k, v in exif_dict.items()
                if k in PIL.ExifTags.TAGS
            }

            # [EXIF: ExifIFD]  CreateDate
            def get_date_for_exif_key(exif_key):
                if exif_key in exif:
                    exif_v = exif[exif_key]
                    if '0000:00:00 00:00:00' != exif_v:
                        try:
                            return datetime.datetime.strptime(exif_v, '%Y:%m:%d %H:%M:%S')
                        except Exception as ex:
                            logging.error("Error on extracting exif date from " +
                                          file_path + ", exif_date: " + exif_v, exc_info=ex)
                            return None

            date_keys = ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']
            date_key_values = list(filter(None, map(get_date_for_exif_key, date_keys)))
            if date_key_values:
                return date_key_values[0]
            else:
                out = None
                if "Date" in str.join(",", exif.keys()):
                    print("===================== Error here, but Date exists")
                    print("path:", file_path)
                    print("exif", exif)
                    print("=====================")

            return out


def add_suffix_to_file(file, exif_date):
    if exif_date:
        suffix = re.sub(r"\D", "", str(exif_date))
    else:
        suffix = "no_exif"
    new_file = file.replace(".", "_" + suffix + "_" + str(current_milli_time()) + ".")
    return new_file


def current_milli_time():
    return int(round(time.time() * 1000))
