import sys
from htmldiff import diff
import utils

def expand_warcs(warc_one_path, warc_two_path, submitted_url_one, submitted_url_two):
    warc_one_index, css_one, js_one, urls_one = utils.get_warc_parts(warc_one_path, submitted_url_one)
    warc_two_index, css_two, js_two, urls_two = utils.get_warc_parts(warc_two_path, submitted_url_two)
    return ((warc_one_index, css_one, js_one, urls_one), (warc_two_index, css_two, js_two, urls_two))

def get_visual_diffs(warc_one_index, warc_two_index, style_str=None):
    """
    returns html text marked up with
    1. deletions, 2. insertions, & 3. both deletions & insertions
    """
    deleted_html, inserted_html, combined_html = diff.text_diff(warc_one_index, warc_two_index)
    return deleted_html, inserted_html, combined_html

def get_simhash_distance(warc_one_index, warc_two_index):
    warc_one_text = utils.html_to_text(warc_one_index)
    warc_two_text = utils.html_to_text(warc_two_index)
    return utils.get_simhash_distance(warc_one_text, warc_two_text)

def get_resource_diffs(warc_one_urls, warc_two_urls):
    missing_resources, added_resources, common_resources = sort_resources(warc_one_urls, warc_two_urls)
    return missing_resources, added_resources, common_resources
