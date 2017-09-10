from htmldiffer import diff

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
        :param urlpath: path of resource to compare
        :param style_str: css to be included in the head of each created html str
            example:
                "<style>
                    span.diff_insert {background-color: #a0ffa0;}
                    span.diff_delete {background-color: #ff7827;}
                </style>"

        :return: html str text marked up with
            1. deletions,
            2. insertions, &
            3. both deletions & insertions
        """
        payload1 = utils.get_payload(urlpath, self.warc1)
        payload2 = utils.get_payload(urlpath, self.warc2)

        decompressed_payload1 = utils.decompress_payload(payload1)
        decompressed_payload2 = utils.decompress_payload(payload2)
        d = diff.HTMLDiffer(decompressed_payload1, decompressed_payload2, style_str=style_str)
        return d.deleted_diff, d.inserted_diff, d.combined_diff

    def calculate_similarity(self, url_pairs=[], minhash=True, simhash=False, sequence_match=False, shingle_settings=shingle_settings):
        compared = dict()
        if len(url_pairs) > 0:
            for pair in url_pairs:
                results = self.calculate_similarity_pair(urls=pair, minhash=minhash, simhash=simhash, sequence_match=sequence_match, shingle_settings=shingle_settings)
                url_str = "%s_%s" % (pair[0],pair[1])
                compared[url_str] = results
        else:
            for content_type in self.resources['modified'].keys():
                for url in self.resources['modified'][content_type]:
                    pair = (url, url)
                    results = self.calculate_similarity_pair(urls=pair, minhash=minhash, simhash=simhash, sequence_match=sequence_match,
                                         shingle_settings=shingle_settings)

                    compared[url] = results
        return compared

    def calculate_similarity_pair(self, urls=(), minhash=True, simhash=False, sequence_match=False, shingle_settings=shingle_settings):
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

        p1 = utils.get_payload(urls[0], self.warc1)
        p2 = utils.get_payload(urls[1], self.warc2)

        dp1 = utils.decompress_payload(p1)
        dp2 = utils.decompress_payload(p2)

        cleaned_dp1 = utils.process_text(dp1)
        cleaned_dp2 = utils.process_text(dp2)

        # shingle cleaned text
        shingles1 = utils.shingle(cleaned_dp1, shingle_settings=shingle_settings)
        shingles2 = utils.shingle(cleaned_dp2, shingle_settings=shingle_settings)

        if minhash:
            compared['minhash'] = utils.get_minhash(shingles1, shingles2)

        if simhash:
            compared['simhash'] = utils.get_simhash(shingles1, shingles2)

        if sequence_match:
            compared['sequence_matched'] = utils.sequence_match(cleaned_dp1, cleaned_dp2)

        return compared

    def count_resources(self):
        nums = dict(modified=0, unchanged=0, missing=0, added=0)

        for resource_type in self.resources:
            count = 0
            for content_type in self.resources[resource_type]:
                count += len(self.resources[resource_type][content_type])
            nums[resource_type] = count

        old_total = nums['modified'] + nums['missing'] + nums['unchanged']
        new_total = nums['modified'] + nums['added'] + nums['unchanged']
        total = (old_total, new_total)

        return [total, nums['unchanged'], nums['missing'], nums['added'], nums['modified']]

    def resource_changed(self, urlpath):
        """
        Returns a boolean according to recorded payload hash
        """
        resource_one = utils.find_resource_by_url(urlpath, self.warc1)
        resource_two = utils.find_resource_by_url(urlpath, self.warc2)
        return resource_one['hash'] != resource_two['hash']
