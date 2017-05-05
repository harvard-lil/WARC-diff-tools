import settings
import sys
from htmldiff import diff
import utils

def _init(warc_one_path, warc_two_path):
    """
    expand warcs into dicts with compressed responses
    organized by content type
    """
    expanded_one = utils.expand_warc(warc_one_path)
    expanded_two = utils.expand_warc(warc_two_path)
    return expanded_one, expanded_two

def get_visual_diffs(urlpath, style_str=None):
    """
    returns html text marked up with
    1. deletions, 2. insertions, & 3. both deletions & insertions
    """
    # TODO: should be able to take in any input (html or not) and spit out html

    if not expanded_one:
        raise

    payload_one = utils.find_resource_by_url(urlpath, expanded_one)
    payload_two = utils.find_resource_by_url(urlpath, expanded_two)

    decompressed_payload_one = utils.decompress_payload(payload_one)
    decompressed_payload_two = utils.decompress_payload(payload_two)

    deleted, inserted, combined = diff.text_diff(decompressed_payload_one, decompressed_payload_two)
    return deleted, inserted, combined

def get_simhash_distance(warc_one_index, warc_two_index):
    warc_one_text = utils.html_to_text(warc_one_index)
    warc_two_text = utils.html_to_text(warc_two_index)
    return utils.get_simhash_distance(warc_one_text, warc_two_text)

def get_similarity(content_type, warc_one, warc_two):
    """
    for content type javascript, for instance:
        get minhash similarity of all, get simhash distance
    """
    # TODO: get combined similarity
    common_resources_compared = dict()
    for url in common_resources:
        common_resources[url] = {minhash:utils.get_minhash(), simhash:simhash}

    return common_resources_compared

def is_resource_changed(urlpath):
    """
    returns a boolean according to recorded payload SHA1
    """
    resource_one = utils.find_resource_by_url(urlpath, expanded_one)
    resource_two = utils.find_resource_by_url(urlpath, expanded_two)
    return resource_one['hash'] == resource_two['hash']
