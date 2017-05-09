import unittest
from utils import *
from fixtures import *

class TestUtils(unittest.TestCase):
    def test_html_to_text(self):
        self.assertTrue("<script>" in example_html_str)
        self.assertTrue("<head>" in example_html_str)

        text_str = html_to_text(example_html_str)
        self.assertFalse("<script>" in text_str)
        self.assertFalse("<head>" in text_str)

    def test_get_simhash(self):
        distance = get_simhash(example_html_str, example_diff_html_str)[0]
        self.assertTrue(distance > 0)

        example_text = html_to_text(example_html_str)
        example_text_2 = html_to_text(example_diff_html_str)

        distance = get_simhash(example_text, example_text_2)[0]
        self.assertEqual(distance, 0)

    def test_sort_resources(self):
        w1 = {
            'text/html': {
                'index.html': {
                    'payload': 'text - html',
                    'hash': '101'
                }
            },
            'image/png': {
                'img.png': {
                    'payload': 'image - png',
                    'hash': '123',
                },
            },
            'application/javascript': {
                'script.js': {
                    'payload': 'js',
                    'hash': 'abc',
                }
            },
        }


        w2 = {
            'image/png': {
                'img2.png': {
                    'payload': 'image - png2',
                    'hash': '234',
                },
            },
            'application/javascript': {
                'script.js': {
                    'payload': 'app - js',
                    'hash': 'abc',
                }
            },
            'text/html': {
                'index.html': {
                    'payload': 'text - html',
                    'hash': '111'
                }
            }
        }

        missing, added, modified, unchanged = sort_resources(w1, w2)
        self.assertTrue('index.html' in modified['text/html'])
        self.assertTrue('img.png' in missing['image/png'])
        self.assertTrue('img2.png' in added['image/png'])
        self.assertEqual(['script.js'], unchanged['application/javascript'])

    def test_is_minified(self):
        minified = is_minified(unminified_script)
        self.assertFalse(minified)
        minified = is_minified(minified_script)
        self.assertTrue(minified)
        minified = is_minified(unminified_script2)
        self.assertFalse(minified)
        minified = is_minified(minified_script2)
        self.assertTrue(minified)
        minified = is_minified(unminified_css)
        self.assertFalse(minified)
        minified = is_minified(minified_css)
        self.assertTrue(minified)

    def test_expand_warc(self):
        warc_path = 'tests/example.warc.gz'
        expanded_warc = expand_warc(warc_path)
        content_types = expanded_warc.keys()
        self.assertTrue("text/html" in content_types)
        self.assertTrue(len(expanded_warc["text/html"].keys()) > 0)

    def test_find_resource_by_url(self):
        warc_path = 'tests/example.warc.gz'
        expanded_warc = expand_warc(warc_path)
        resource = find_resource_by_url("http://example.com/robots.txt", expanded_warc)
        self.assertTrue("hash" in resource)
        self.assertTrue("payload" in resource)

    def test_decompress_payload(self):
        warc_path = 'tests/example.warc.gz'
        expanded_warc = expand_warc(warc_path)
        resource = find_resource_by_url("http://example.com/robots.txt", expanded_warc)
        compressed_payload = resource["payload"]
        self.assertFalse("<h1>Example Domain</h1>" in compressed_payload)
        decompressed_payload = decompress_payload(compressed_payload)
        self.assertTrue("<h1>Example Domain</h1>" in decompressed_payload)

def main():
    unittest.main()

if __name__ == '__main__':
    main()
