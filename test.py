import datetime

import nm_tools


def test_get_date_from_string():
    pat1 = r"(\D)(?P<day>\d{2})(\1)(?P<month>\d{2})(\1)(?P<year>20\d{2})(\1)"
    assert nm_tools.get_date_from_string(pat1, "/10/02/2021/") == (2021, 2, 10)
    assert nm_tools.get_date_from_string(pat1, "/10/02/2021/") == (2021, 2, 10)
    assert nm_tools.get_date_from_string(pat1, "/10/02/1021/") is None

    pat2 = r"(\D)(?P<year>20\d{2})(\1)(?P<month>\d{2})(\1)(?P<day>\d{2})(\1)"
    assert nm_tools.get_date_from_string(pat2, "/2021/02/10/") == (2021, 2, 10)

    pat3 = r"(\W)(?P<day>\d{1,2})(\W)(?P<month>\w+)(\W)(?P<year>20\d{2})(\W)"
    assert nm_tools.get_date_from_string(pat3, "/2314, 10 February 2021 234/") == (2021, 2, 10)
    assert nm_tools.get_date_from_string(pat3, "/2314, 2 June 2011 234/") == (2011, 6, 2)
    assert nm_tools.get_date_from_string(pat3, "/2314, 02 June 2011 234/") == (2011, 6, 2)
    assert nm_tools.get_date_from_string(pat3, "/2314, 31 June 2011 234/") == (2011, 6, 31)
    assert nm_tools.get_date_from_string(pat3, "/2314, 32 June 2011 234/") is None
    assert nm_tools.get_date_from_string(pat3, "/2314, 00 June 2011 234/") is None


def test_get_date_from_numbered_folder_path():
    assert nm_tools.get_date_from_path("/1/2021/02/10/") \
           == datetime.datetime(2021, 2, 10)
    assert nm_tools.get_date_from_path("/10/02/2021/") \
           == datetime.datetime(2021, 2, 10)
    # with month as a word
    assert nm_tools.get_date_from_path("/Home, 14 December 2020/") \
           == datetime.datetime(2020, 12, 14)
    assert nm_tools.get_date_from_path("/4 March 2021 ") \
           == datetime.datetime(2021, 3, 4)
    assert nm_tools.get_date_from_path("/23 April 2019/") \
           == datetime.datetime(2019, 4, 23)
    assert nm_tools.get_date_from_path("/21 January 2017/2017-01-21_14.jpg") \
           == datetime.datetime(2017, 1, 21)
    assert nm_tools.get_date_from_path("/21 January 2017/2018-01-21_14.jpg") \
           == datetime.datetime(2018, 1, 21)
    assert nm_tools.get_date_from_path("/Volumes/photo/byYears/1904/01/01/2020-11-20_0.mp4") \
           == datetime.datetime(2020, 11, 20)


def test_get_file_datetime():
    import get_folder_structure_and_convert_to_nas_format
    print(get_folder_structure_and_convert_to_nas_format
          .get_file_datetime("/Volumes/photo/unknown2/2019-06-25_15-01-19.JPG"))
