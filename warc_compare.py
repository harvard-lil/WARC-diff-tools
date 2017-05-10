import sys
from htmldiff import diff

from toggles import shingle_settings
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
        payload1 = utils.get_payload(urlpath, self.warc1)
        payload2 = utils.get_payload(urlpath, self.warc2)

        decompressed_payload1 = utils.decompress_payload(payload1)
        decompressed_payload2 = utils.decompress_payload(payload2)

        deleted, inserted, combined = diff.text_diff(decompressed_payload1, decompressed_payload2)
        return deleted, inserted, combined

    def calculate_similarity(self, shingle_settings=shingle_settings):
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
        compared = dict()
        for content_type in self.resources['modified'].keys():
            for url in self.resources['modified'][content_type]:
                resource_changed = self.resource_changed(url)
                compared[url] = {
                    "hash_change": resource_changed
                }

                if "image" in content_type:
                    continue

                if resource_changed:
                    p1 = utils.get_payload(url, self.warc1)
                    p2 = utils.get_payload(url, self.warc2)

                    dp1 = utils.decompress_payload(p1)
                    dp2 = utils.decompress_payload(p2)

                    cleaned_dp1 = utils.process_text(dp1)
                    cleaned_dp2 = utils.process_text(dp2)

                    # shingle cleaned text
                    shingles1 = utils.shingle(cleaned_dp1, shingle_settings=shingle_settings)
                    shingles2 = utils.shingle(cleaned_dp2, shingle_settings=shingle_settings)

                    compared[url]['minhash'] = utils.get_minhash(shingles1, shingles2)
                    compared[url]['simhash'] = utils.get_simhash(shingles1, shingles2)

        return compared

    def resource_changed(self, urlpath):
        """
        Returns a boolean according to recorded payload hash
        """
        resource_one = utils.find_resource_by_url(urlpath, self.warc1)
        resource_two = utils.find_resource_by_url(urlpath, self.warc2)
        return resource_one['hash'] != resource_two['hash']
