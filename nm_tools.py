import datetime
import filecmp
import hashlib
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


def compare_files(filename1, filename2):
    return filecmp.cmp(filename1, filename2)


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
    out = datetime.datetime(year=f_year, month=f_month, day=f_day)
    return out


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
            if 'DateTime' in exif:
                exif_d = exif['DateTime']
                if '0000:00:00 00:00:00' == exif_d:
                    out = None
                else:
                    out = datetime.datetime.strptime(exif_d, '%Y:%m:%d %H:%M:%S')
            else:
                out = None
                if "Date" in str.join(",", exif.keys()):
                    print(file_path)
                    print(exif)
                    print("Error here, but Date exists")

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
