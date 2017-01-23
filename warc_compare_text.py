import warc
import zlib
import simhash
import re
from httplib import HTTPResponse
from StringIO import StringIO

warc_one = "6T9V-CQA3.warc.gz"
warc_two = "8MFU-BES4.warc.gz"

class FakeSocket():
    def __init__(self, response_str):
        self._file = StringIO(response_str)
    def makefile(self, *args, **kwargs):
        return self._file

def warc_to_dict(warc_filename):
    # getting only first response (html) for now
    warc_open = warc.open(warc_filename)
    response = dict()
    for record in warc_open:
        if record.type == 'warcinfo':
            response['warcinfo'] = record
            response['warcinfo_payload'] = record.payload.read()
        if record.type == 'response':
            response['record'] = record
            response['payload'] = record.payload.read()
            break
    return response

def payload_to_text(payload):
    # includes anything inside of script tags as if it's in dom
    # maybe that should be changed
    rx = re.compile('<\s*\w.*?>|</\s*\w.*?>|\n|\t|\r|\s{2}')
    source = FakeSocket(payload)
    res = HTTPResponse(source)
    res.begin()
    result = zlib.decompress(res.read(), 16+zlib.MAX_WBITS)
    return rx.sub('',result)

def get_distance(str_one, str_two):
    return simhash.Simhash(str_one).distance(simhash.Simhash(str_two))
