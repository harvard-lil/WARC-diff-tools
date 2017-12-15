from dashboard.utils import *


def test_rewrite_html():
    warc_dir = "path-to-warc-dir"
    html = '<a href="http://localhost/path-to-warc-dir">here is a link!</a>'
    res = rewrite_html(html, warc_dir)

    assert res != html
    assert '/archives/path-to-warc-dir">here is a link!</a>' in res

