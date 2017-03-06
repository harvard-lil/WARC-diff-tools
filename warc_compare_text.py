import sys
import warc
import zlib
import simhash
import csv
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
    # TODO: check if stream
    warc_open = warc.open(warc_filename)
    response = {'records' : {}, 'payload': []}

    for record in warc_open:
        if record.type == 'warcinfo':
            response['warcinfo'] = record
            response['warcinfo_payload'] = record.payload.read()
        if record.type == 'response':
            # TODO: can records have the same url?
            response['records'][record.url] = ''
            payload = record.payload.read()
            try:
                source = FakeSocket(payload)
                res = HTTPResponse(source)
                res.begin()
                result = zlib.decompress(res.read(), 16+zlib.MAX_WBITS)
                # result = zlib.decompress(res.read(), zlib.MAX_WBITS|16)
                response['records'][record.url] = payload
            except Exception as e:
                # print e
                try:
                    response['records'][record.url] = '.'.join(str(ord(c)) for c in payload)
                except:
                    response['records'][record.url] = payload
                    pass
                pass
    return response

def get_index_page_payload(site, warc_response_dict):
    for idx,rec in enumerate(warc_response_dict['record']):
        if site in rec.header.values():
            return idx

def payload_to_text(payload):
    # includes anything inside of script tags as if it's in dom
    # maybe that should be changed
    rx = re.compile('<\s*\w.*?>|</\s*\w.*?>|\n|\t|\r|\s{2}')
    return rx.sub('',payload)

"""
name
request number
url 'payload matches (True/False)'  'text matches (True/False)' 'distance (simhash)'
"""
def get_distance(str_one, str_two):
    try:
        res =  simhash.Simhash(str_one).distance(simhash.Simhash(str_two))
    except:
        res = None
        pass
    finally:
        return res

def compare_warcs(w1, w2):
    d1 = warc_to_dict(w1)
    d2 = warc_to_dict(w2)

    filename = "%s_v_%s.csv" % (w1.split('/')[-1], w2.split('/')[-1])
    print filename
    fieldnames = ['url', 'payload_match', 'text_match', 'simhash_distance', 'missing']
    records1 = d1['records']
    records2 = d2['records']
    with open(filename, 'a') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for url in records1.keys():
            if records2.get(url):
                payload_match = records1[url] == records2[url]
                text1 = payload_to_text(records1[url])
                text2 = payload_to_text(records2[url])
                text_match = text1 == text2
                distance = get_distance(text1, text2)
                writer.writerow({'url': url, 'payload_match': payload_match, 'text_match': text_match, 'simhash_distance': distance, 'missing':''})
            else:
                writer.writerow({'url': url, 'payload_match': False, 'text_match': False, 'simhash_distance': '', 'missing': True})
if __name__ == '__main__':
    compare_warcs(sys.argv[1], sys.argv[2])
