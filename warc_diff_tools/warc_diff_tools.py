import settings
import sys
from htmldiff import diff
import utils

class WARCComparison:
    def __init__(self, warc1_path, warc2_path):
        self.warc1 = utils.expand_warc(warc1_path)
        self.warc2 = utils.expand_warc(warc2_path)
        self.missing_resources, self.added_resources, self.common_resources = utils.sort_resources(self.warc1, self.warc2)

    def has_resource_changed(self, urlpath):
        """
        Returns a boolean according to recorded payload hash
        """
        resource_one = utils.find_resource_by_url(urlpath, self.warc1)
        resource_two = utils.find_resource_by_url(urlpath, self.warc2)
        return resource_one['hash'] == resource_two['hash']

    def get_visual_diffs(self, urlpath, style_str=None):
        """
        Returns html text marked up with
        1. deletions, 2. insertions, & 3. both deletions & insertions
        """
        # TODO: should be able to take in any input (html or not) and spit out html
        payload1 = utils.find_resource_by_url(urlpath, self.warc1)
        payload2 = utils.find_resource_by_url(urlpath, self.warc2)

        decompressed_payload1 = utils.decompress_payload(payload1)
        decompressed_payload2 = utils.decompress_payload(payload2)

        deleted, inserted, combined = diff.text_diff(decompressed_payload1, decompressed_payload2)
        return deleted, inserted, combined

    def get_similarity(self, content_type):
        """
        For content type javascript, for instance:
            get minhash similarity of all, get simhash distance
        """
        # TODO: WIP! 
        # TODO: get combined similarity
        common_resources_compared = dict()
        for url in common_resources:
            common_resources[url] = {minhash:utils.get_minhash(), simhash:utils.get_simhash_distance(warc_one_text, warc_two_text)}

        return common_resources_compared
