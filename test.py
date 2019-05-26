import nm_tools


def test_get_date_from_folder_path():
    path = "/Volumes/for-import-on-nas/Katya/Fotki/2011Leto/C360_2011-06-30_20-14-39.jpg"
    nm_tools.get_file_datetime(path)
