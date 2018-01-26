import re

from django.conf import settings
import minhash
from toggles import hashfunc, simhash_bytes, shingle_settings, minhash_hash_num
from htmldiffer import diff

#
# class FakeSocket():
#     def __init__(self, response_str):
#         self._file = StringIO(response_str)
#     def makefile(self, *args, **kwargs):
#         return self._file
#
#
# def html_to_text(html_str):
#     soup = BeautifulSoup(html_str, "html.parser")
#     [s.extract() for s in soup('script')]
#     return soup.body.getText()
#
#
# def is_minified(script):
#     """
#     !!! HACKY APPROXIMATION !!!
#     - if has high line count and low char count
#       and if includes newlines, tabs, returns, and more than two spaces,
#     in second half of script (allowing for copyright notices / authoring comments)
#     not likely to be minified
#     - for js if params have chars with length > 3, not likely to be minified
#     """
#     high_char_count = False
#     halved_script = script[len(script)/2:]
#     whitespaces_found = len(re.compile('\n|\t|\r|\s{2}').findall(halved_script)) > 2
#
#     lines = script.split('\n')
#     low_line_count = len(lines) < 500
#
#     for line in lines:
#         if len(line) > 500:
#             high_char_count = True
#             break
#
#     try:
#         params_found = re.compile('function\s+\w+\(\w{3,}').search(halved_script).group()
#     except AttributeError:
#         params_found = False
#
#     return params_found or not whitespaces_found or (low_line_count and high_char_count)
#
# def get_simhash(shingles1, shingles2, simhash_bytes=simhash_bytes, hashfunc=hashfunc):
#     sim1 = simhash(shingles1, hashbits=simhash_bytes)
#     sim2 = simhash(shingles2, hashbits=simhash_bytes)
#
#     return sim1.similarity(sim2)
#
#

def decode_data(data):
    try:
        return data.decode()
    except UnicodeDecodeError:
        return data.decode('latin-1')


def shingle(text, shingle_settings=shingle_settings):
    """
    tokenizes and shingles

    chooses window size according to ruleset
    automatically shingles minified css and js by character
    everything else is shingled by word (space)

    """
    shingles = set()
    shingle_type = shingle_settings['shingle_type']
    if not shingle_type:
        if is_minified(text):
            shingle_type = 'char'
        else:
            shingle_type = 'word'

    if shingle_type == 'char':
        units = list(text)
    else:
        units = text.split()

    shingle_size = shingle_settings[shingle_type]

    for idx in range(0, len(units) - (shingle_size - 1)):
        if shingle_type == 'word':
            shingle = ' '.join(units[idx:idx+shingle_size])
        else:
            shingle = ''.join(units[idx:idx+shingle_size])

        shingles.add(shingle)

    return shingles


def process_text(text):
    # TODO: add rules per content_type
    rx = re.compile('\s{2}')
    text = rx.sub('', text)
    # try:
    #     text = unicode(text, 'utf-8')
    # except (UnicodeEncodeError, UnicodeDecodeError) as e:
    #     text = text.decode('utf-8', 'ignore')

    return text.lower()


def get_minhash(str1, str2):
    return minhash.calculate(str1, str2, total_hash_num=minhash_hash_num)

#
# def get_combined_distance(str1, str2):
#     return
#
#
# def decompress_payload(payload):
#     try:
#         source = FakeSocket(payload)
#         res = HTTPResponse(source)
#         res.begin()
#         result = zlib.decompress(res.read(), 16+zlib.MAX_WBITS)
#     except Exception as e:
#         result = payload
#         # try:
#         #     result = '.'.join(str(ord(c)) for c in payload)
#         # except:
#         #     result = payload
#     return result
#
#
def sort_resources(archive1_expanded, archive2_expanded):
    """
    sorting dictionaries of collections into:
        - missing (no longer available)
        - added (newly added since first capture)
        - modified (common resources that whose hashes are unequal)
        - unchanged
    """

    missing, added, modified, unchanged = dict(), dict(), dict(), dict()

    for key in archive1_expanded.keys():
        if key not in archive2_expanded.keys():
            missing[key] = set(archive1_expanded[key])
        else:
            set_a = set(archive1_expanded[key])
            set_b = set(archive2_expanded[key])

            common = list(set_a & set_b)

            missing[key] = list(set_a - set_b)
            added[key] = list(set_b - set_a)

            if len(missing[key]) == 0:
                missing.pop(key, None)

            if len(added[key]) == 0:
                added.pop(key, None)

            for url in common:
                hashes_are_equal = archive1_expanded[key][url]['hash'] == archive2_expanded[key][url]['hash']
                if hashes_are_equal:
                    if key in unchanged:
                        unchanged[key].append(url)
                    else:
                        unchanged[key] = [url]
                else:
                    if key in modified:
                        modified[key].append(url)
                    else:
                        modified[key] = [url]

    return missing, added, modified, unchanged
#
#
def get_payload_headers(payload):
    """
    return resource's recorded header
    """
    header_dict = dict()
    headers = payload.split('\r\n\r\n')[0].split('\n')
    for head in headers:
        if ":" in head:
            try:
                key, val = head.split(": ",1)
                header_dict[key] = val
            except:
                key = head.split(":", 0)
                val = ""
    return header_dict
#
#
# def expand_warc(warc_path):

def find_resource_by_url(urlpath, expanded_warc):
    """
    returns { "payload": decompressed_payload, "hash":"sha1" }
    """
    for content_type in expanded_warc:
        urls = expanded_warc[content_type].keys()
        if urlpath in urls:
            return expanded_warc[content_type][urlpath]


def get_payload(urlpath, expanded_warc):
    return find_resource_by_url(urlpath, expanded_warc)['payload'].decode()


def rewrite_html(html_page, warc_dir):
    # TODO: build this out
    tmp_html = re.sub("http://localhost/", "%s://%s%s/" % (settings.PROTOCOL, settings.BASE_URL, settings.ARCHIVES_ROUTE), html_page)
    return re.sub(warc_dir, "archives/{0}".format(warc_dir), tmp_html)


def format_content_type(content_type):
    """
    removes parameter and whitespaces
    should only return type/subtype
    e.g. 'text/html' and 'application/javascript'
    """
    rx = re.compile('\n|\t|\r')
    return rx.sub('', content_type).split(';')[0]

#
# def sequence_match(s1, s2):
#     seq = difflib.SequenceMatcher(None, s1, s2)
#     return seq.ratio() * 100


def get_html_diff(payload1, payload2):
    d = diff.HTMLDiffer(payload1, payload2)
    return d.deleted_diff, d.inserted_diff, d.combined_diff


def calculate_similarity_pair(payload1, payload2, minhash=True, simhash=False, sequence_match=False, shingle_settings=shingle_settings):
    """
    checking all common resources for changes
    image checking is broken for now, requires a separate handling

    :param minhash: True or False, default True
    :param simhash: True or False, default True
    :param sequence_match: True or False, default True
    :param shingle_settings: see `shingle_settings` in toggles.py

    :return:
        { resource_url_path:
            "hash_change" : True or False (sha1 change)
            "minhash": minhash_coefficient,
            "simhash": simhash_distance,
        }
    """
    compared = dict()

    cleaned_p1 = process_text(payload1)
    cleaned_p2 = process_text(payload2)

    # shingle cleaned text
    shingles1 = shingle(cleaned_p1, shingle_settings=shingle_settings)
    shingles2 = shingle(cleaned_p2, shingle_settings=shingle_settings)

    if minhash:
        compared['minhash'] = get_minhash(shingles1, shingles2) * 100

    # if simhash:
    #     compared['simhash'] = get_simhash(shingles1, shingles2)
    #
    # if sequence_match:
    #     compared['sequence_matched'] = sequence_match(cleaned_dp1, cleaned_dp2)

    return compared
