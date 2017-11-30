from dashboard.utils import *


def test_url_to_dirname():
    url = "http://example.com"
    res = url_to_dirname(url)
    assert res == "example_com"
    url = "https://lil.law.harvard.edu/collaborate/2018/summer/fellows/apply"
    res = url_to_dirname(url)
    assert res == "lil_law_harvard_edu_collaborate_2018_summer_fellows_apply"

