import os
import re
from urllib.parse import urlparse
from datetime import datetime

from django.conf import settings


def format_date_for_memento(date_string):
    d = datetime.strptime(date_string, '%Y-%m-%d')
    return d.strftime('%Y%m%d')


def url_to_dirname(submitted_url):
    """
    Make a directory-friendly url name
    http://example.com should return example_com
    """
    url_parts = urlparse(submitted_url)
    domain = url_parts.netloc.replace(".", "_")
    path = url_parts.path.replace("/", "_")
    query = url_parts.query.replace("=", "_")
    return domain + path + query


def get_full_warc_path(archive_dirname):
    """
    Takes named archive dir (should consist of timestamp_submitted_url)
    Returns full path to warc (should have a single warc per directory)
    """
    full_archive_parent_path = settings.COLLECTIONS_DIR + "/" + archive_dirname + "/archive"
    assert os.path.exists(full_archive_parent_path)
    warc_name = os.listdir(full_archive_parent_path)[0]
    assert "warc.gz" in warc_name
    warc_path = full_archive_parent_path + '/' + warc_name
    assert os.path.exists(warc_path)
    return warc_path


def rewrite_html(html_page, warc_dir):
    # TODO: build this out
    tmp_html = re.sub('"%s' % warc_dir, '"archives/%s' % (settings.BASE_URL, warc_dir), html_page)
    # tmp_html = re.sub("localhost:8082/%s" % warc_dir, "localhost:8082/archives/%s" % warc_dir, tmp_html)
    # tmp_html = re.sub("localhost/", "localhost:8082/", tmp_html)
    # tmp_html = re.sub('href="//localhost', 'href="http://localhost', tmp_html)
    return re.sub("%s" % settings.BASE_URL, "%s/archives/" % settings.BASE_URL, tmp_html)


def write_to_static(new_string, filename, compare_id=None):
    dirpath = create_compare_dir(str(compare_id))
    filepath = os.path.join(dirpath, filename)
    with open(filepath, 'w+') as f:
        f.write(new_string)

    print("wrote %s to static: %s" % (filename, filepath))


def create_compare_dir(compare_id):
    dirpath = os.path.join(settings.STATIC_DIR, compare_id)
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    return dirpath


def get_compare_dir_path(compare_id):
    return os.path.join(settings.STATIC_DIR, compare_id)
