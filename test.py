import nm_tools


def test_get_date_from_folder_path():
    path = "/Volumes/for-import-on-nas/from-Katya-folder-output/unknown/IMG_0161.PNG"
    check = nm_tools.get_file_datetime(path)
    print(check)
