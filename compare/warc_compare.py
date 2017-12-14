from htmldiffer import diff

from toggles import shingle_settings
from compare import utils

archive1_path = "/Users/aaizman/Documents/WARC-diff-tools/collections/20030110_example_com/archive/warc-diff-20171130212034161210-RSJ3M2I2.warc.gz"
archive2_path = "/Users/aaizman/Documents/WARC-diff-tools/collections/20000110_example_com/archive/warc-diff-20171130210938217967-HKIUU7FF.warc.gz"

class WARCCompare:
    def __init__(self, archive1_path, archive2_path):
        self.archive1 = utils.expand_warc(archive1_path)
        self.archive2 = utils.expand_warc(archive2_path)

        missing, added, modified, unchanged = utils.sort_resources(self.archive1, self.archive2)

        self.resources = {
            'missing': missing,
            'added': added,
            'modified': modified,
            'unchanged': unchanged,
        }

    def get_visual_diffs(self, urlpath, urlpath2):
        """
        :param urlpath: path of resource to compare
        :param urlpath2: path of second resource to compare, if the path is different

        :return: html str text marked up with
            1. deletions,
            2. insertions, &
            3. both deletions & insertions
        """
        if not urlpath2:
            urlpath2 = urlpath

        payload1 = utils.get_payload(urlpath, self.archive1)
        payload2 = utils.get_payload(urlpath2, self.archive2)

        d = diff.HTMLDiffer(payload1, payload2)

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

        p1 = utils.get_payload(urls[0], self.archive1)
        p2 = utils.get_payload(urls[1], self.archive2)

        cleaned_p1 = utils.process_text(p1)
        cleaned_p2 = utils.process_text(p2)

        # shingle cleaned text
        shingles1 = utils.shingle(cleaned_p1, shingle_settings=shingle_settings)
        shingles2 = utils.shingle(cleaned_p2, shingle_settings=shingle_settings)

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
        resource_one = utils.find_resource_by_url(urlpath, self.archive1)
        resource_two = utils.find_resource_by_url(urlpath, self.archive2)
        return resource_one['hash'] != resource_two['hash']
