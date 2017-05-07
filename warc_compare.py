import time
import sys
from htmldiff import diff
import utils

class WARCCompare:
    def __init__(self, warc1_path, warc2_path):
        self.warc1 = utils.expand_warc(warc1_path)
        self.warc2 = utils.expand_warc(warc2_path)

        missing, added, modified, unchanged = utils.sort_resources(self.warc1, self.warc2)

        self.resources = {
            'missing': missing,
            'added': added,
            'modified': modified,
            'unchanged': unchanged,
        }

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

    def calculate_similarity(self):
        """
        - checking all common resources for changes
        - only including sha1 check for images for now
        output:
            { resource_url_path:
                "hash_change" : True or False (sha1 change)
                "minhash": minhash_coefficient,
                "simhash": simhash_distance,
            }
        """
        # TODO: get combined similarity
        compared = dict()
        start_time = time.time()
        for content_type in self.common_resources.keys():
            for url in self.common_resources[content_type]:
                resource_changed = self.resource_changed(url)
                compared[url] = {
                    "hash_change": resource_changed
                }

                if "image" in content_type:
                    continue

                if resource_changed:
                    p1 = utils.find_resource_by_url(url, self.warc1)['payload']
                    p2 = utils.find_resource_by_url(url, self.warc2)['payload']

                    dp1 = utils.decompress_payload(p1)
                    dp2 = utils.decompress_payload(p2)

                    compared[url]['minhash'] = utils.get_minhash(dp1, dp2)
                    compared[url]['simhash'] = utils.get_simhash_distance(dp1, dp2)

        return compared

    def resource_changed(self, urlpath):
        """
        Returns a boolean according to recorded payload hash
        """
        resource_one = utils.find_resource_by_url(urlpath, self.warc1)
        resource_two = utils.find_resource_by_url(urlpath, self.warc2)
        return resource_one['hash'] != resource_two['hash']
