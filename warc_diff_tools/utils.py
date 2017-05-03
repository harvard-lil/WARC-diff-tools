import os
import re
import urlparse
import warc
from httplib import HTTPResponse
from StringIO import StringIO
import zlib
import minhash
import simhash
from bs4 import BeautifulSoup

class FakeSocket():
    def __init__(self, response_str):
        self._file = StringIO(response_str)
    def makefile(self, *args, **kwargs):
        return self._file

def html_to_text(html_str):
    soup = BeautifulSoup(html_str, "html.parser")
    [s.extract() for s in soup('script')]
    return soup.body.getText()

def is_unminified(script_str, type_of_script):
    """
        if includes newlines, tabs, returns, and more than two spaces,
        not likely to be minified
    """
    whitespaces_found = len(re.compile('\n|\t|\r|\s{2}').findall(script_str)) > 1

    if type_of_script == "css":
        return whitespaces_found

    elif type_of_script == "js":
        # minifiers reduce params to single letters
        try:
            params_found = re.compile('function\s+\w+\(\w{3,}').search(script_str).group()
        except:
            params_found = None

        if params_found:
            return True

        return whitespaces_found

def get_comparison(str_one, str_two, algorithm="simhash"):
    rx = re.compile('\n|\t|\r|\s{2}')
    cleaned_one = rx.sub(' ', str_one)
    cleaned_two = rx.sub(' ', str_two)

    if algorithm == "simhash":
        return get_simhash_distance(str_one, str_two)
    elif algorithm == "minhash":
        return minhash.get_minhash(cleaned_one, cleaned_two)
    elif algorithm == "mix":
        get_combined_distance(str_one, str_one)

def get_simhash_distance(str_one, str_two):
    try:
        res = simhash.Simhash(str_one).distance(simhash.Simhash(str_two))
    except:
        res = None
        pass
    finally:
        return res


def get_combined_distance(str_one, str_two):
    return

def warc_to_dict(warc_filename):
    # TODO: check if stream
    warc_open = warc.open(warc_filename)
    response = {}

    for record in warc_open:
        payload = decompress_payload(record.payload.read(), record.type, record.url)

        if record.type in response:
            if record.url in response[record.type]:
                response[record.type][record.url].append(payload)
            else:
                response[record.type][record.url] = [payload]
        else:
            response[record.type] = {record.url:[payload]}

def decompress_payload(payload):
    try:
        source = FakeSocket(payload)
        res = HTTPResponse(source)
        res.begin()
        result = zlib.decompress(res.read(), 16+zlib.MAX_WBITS)
    except Exception as e:
        # print record_type, record_url
        result = payload
        # try:
        #     result = '.'.join(str(ord(c)) for c in payload)
        # except:
        #     result = payload
    return result

def sort_resources(collection_one, collection_two):
    """
    sorting dictionaries of collections into:
        - missing (no longer available),
        - added (newly added since first capture), and
        - common (seen in both)
    """

    missing_resources, added_resources, common_resources = dict(), dict(), dict()

    for key in collection_one.keys():
        set_a = set(collection_one[key])
        set_b = set(collection_two[key])
        common_resources[key] = list(set_a & set_b)
        missing_resources[key] = list(set_a - set_b)
        added_resources[key] = list(set_b - set_a)

    return missing_resources, added_resources, common_resources


def get_warc_parts(warc_path, submitted_url):
    warc_open = warc.open(warc_path)
    response_urls, css, js = dict(), dict(), dict()
    payload = ''

    for record in warc_open:
        if record.type == 'response':
            path = urlparse.urlparse(record.url).path
            ext = os.path.splitext(path)[1]
            if record.url[:-1] == submitted_url or record.url == submitted_url:
                payload = decompress_payload(record.payload.read())
                ext = 'index'

            if ext == ".css":
                css[record.url] = decompress_payload(record.payload.read())
            if ext == ".js":
                js[record.url] = decompress_payload(record.payload.read())

            if ext in response_urls:
                response_urls[ext].append(record.url)
            else:
                response_urls[ext] = [record.url]

    return payload, css, js, response_urls
