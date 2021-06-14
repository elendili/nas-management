import datetime
import filecmp
import hashlib
import logging
import re
import time
from os.path import (getmtime, exists, splitext)

import PIL.ExifTags
import PIL.Image
import filetype
import hachoir.core
import hachoir.metadata
import hachoir.parser

count_of_days_to_use_for_native_file_modification_date = 5
hachoir.core.config.quiet = True


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


def get_file_modification_date(file_path) -> datetime.datetime:
    mtime = getmtime(file_path)
    out = datetime.datetime.fromtimestamp(mtime)
    period = out - datetime.datetime.now()
    if abs(period.days) > count_of_days_to_use_for_native_file_modification_date:
        return out
    else:
        return None


def get_file_datetime(file_path) -> datetime.datetime:
    if not exists(file_path):
        raise FileNotFoundError(file_path)

    hachoir_date = get_creation_date_by_harchoir(file_path)
    if hachoir_date:
        return hachoir_date

    exif_date = get_exif_date(file_path)
    if exif_date:
        return exif_date

    file_modification_date = get_file_modification_date(file_path)
    if file_modification_date:
        return file_modification_date

    folder_date = get_date_from_numbered_folder_path(file_path)
    if folder_date:
        return folder_date

    logging.error("No exif or folder date to extract for " + file_path)


def get_file_extension(file_path) -> str:
    guessed = filetype.guess(file_path)
    if guessed:
        return "." + guessed.extension
    else:
        return splitext(file_path)[-1]


def get_date_from_string(pattern, string):
    try:
        f = re.search(pattern, string)
        if f:
            m = f.group("month")
            if m.isnumeric():
                month = int(m)
            else:
                month = datetime.datetime.strptime(m, "%B").month

            d = f.group("day")
            day = datetime.datetime.strptime(d, "%d").day

            return int(f.group("year")), month, day
    except:
        return None


def get_date_from_numbered_folder_path(file_path):
    file_path = str(file_path)
    pat1 = r"(\D)(?P<day>\d{2})(\1)(?P<month>\d{2})(\1)(?P<year>20\d{2})(\1)"
    pat2 = r"(\D)(?P<year>20\d{2})(\1)(?P<month>\d{2})(\1)(?P<day>\d{2})(\1)"
    pat3 = r"(\W)(?P<day>\d{1,2})(\W)(?P<month>\w+)(\W)(?P<year>20\d{2})(\W)"
    found1 = get_date_from_string(pat1, file_path)
    found2 = get_date_from_string(pat2, file_path)
    found3 = get_date_from_string(pat3, file_path)
    if found1:
        f_year, f_month, f_day = found1
    elif found2:
        f_year, f_month, f_day = found2
    elif found3:
        f_year, f_month, f_day = found3
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
    upper_path = file_path.upper()
    if (not upper_path.endswith(".MOV")
            and not upper_path.endswith(".PNG")
            and not upper_path.endswith(".CR2")
            and not upper_path.endswith(".HEIC")
            and not upper_path.endswith(".AAE")
    ):
        try:
            img = PIL.Image.open(file_path)
            if hasattr(img, "_getexif"):
                exif_dict = img._getexif()
            else:
                logging.error("no exif data on:", file_path)
                return None
        except Exception as e:
            logging.error(file_path, exc_info=e)
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
                    exif_v = re.sub(r"\D+$", "", exif_v)  # remove tail garbage
                    exif_v = re.sub(r"^\D+", "", exif_v)  # remove head garbage
                    if '0000:00:00 00:00:00' != exif_v:
                        try:
                            return datetime.datetime.strptime(exif_v,
                                                              '%Y:%m:%d %H:%M:%S')
                        except Exception as ex:
                            logging.error(
                                "Error on extracting exif date from " +
                                file_path + ", exif_date: " + exif_v,
                                exc_info=ex)
                            return None

            date_keys = ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']
            date_key_values = list(
                filter(None, map(get_date_for_exif_key, date_keys)))
            if date_key_values:
                return date_key_values[0]
            else:
                if "Date" in str.join(",", exif.keys()):
                    logging.error("===================== Error here, but Date exists",
                                  "path:", file_path, "exif", exif, "=====================")

            return None


def add_suffix_to_file(file, exif_date):
    if exif_date:
        suffix = re.sub(r"\D", "", str(exif_date))
    else:
        suffix = "no_exif"
    new_file = file.replace(".", "_" + suffix + "_" + str(
        current_milli_time()) + ".")
    return new_file


def current_milli_time():
    return int(round(time.time() * 1000))


def get_creation_date_by_harchoir(filename):
    meta = get_metadata_by_harchoir(filename)
    if meta and meta.has('creation_date'):
        return meta.get('creation_date')
    return None


# import hachoir.metadata.metadata

def get_metadata_by_harchoir(filename) -> hachoir.metadata.metadata:
    try:
        parser = hachoir.parser.createParser(filename)
        return hachoir.metadata.extractMetadata(parser)
    except Exception as e:
        logging.error("hachoir can't extract metadata", e)
        return None
