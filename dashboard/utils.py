from urllib.parse import urlparse
from datetime import datetime


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
