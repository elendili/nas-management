import datetime
import filecmp
import hashlib
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


def compare_files(filename1, filename2):
    return filecmp.cmp(filename1, filename2)


def get_date_from_folder_path(target_folder, file_path):
    try:
        for_extract = str(file_path).replace(target_folder, "")
        # print(for_extract)
        for_extract2 = list(filter(None, for_extract.split(os.sep)))[:3]
        # print(for_extract2)
        f_year, f_month, f_day = map(int, for_extract2)
        # print(f_year, f_month, f_day)
        out = datetime.datetime(year=f_year, month=f_month, day=f_day)
        return out
    except Exception as e:
        print(e)
        return None


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


def connect():
    import spur
    connection_data = {"hostname": "192.168.1.36", "username": "elendili",
                       "private_key_file": "/Users/elendili/.ssh/id_rsa"}
    with spur.SshShell(**connection_data) as shell:
        result = shell.run(["pwd"])
        print(result.output)
        result = shell.run(["ls"])
        print(str(result.output).split("\\n"))
        result = shell.run(["cp", "-l", "process_duplicates.py", "process_duplicates.py2"])
        print(str(result.output).split("\\n"))

#
# if __name__ == '__main__':
#     connect()
