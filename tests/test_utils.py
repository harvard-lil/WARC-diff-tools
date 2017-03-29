import unittest
import re
from utils import html_to_text, get_simhash_distance
from fixtures import example_html_str, example_diff_html_str

class TestUtilsBs(unittest.TestCase):
    def test_html_to_text(self):
        self.assertTrue("<script>" in example_html_str)
        self.assertTrue("<head>" in example_html_str)

        text_str = html_to_text(example_html_str)
        self.assertFalse("<script>" in text_str)
        self.assertFalse("<head>" in text_str)

    def test_get_simhash_distance(self):
        distance = get_simhash_distance(example_html_str, example_diff_html_str)
        self.assertTrue(distance > 0)

        example_text = html_to_text(example_html_str)
        example_text_2 = html_to_text(example_diff_html_str)
        distance = get_simhash_distance(example_text, example_text_2)
        self.assertEqual(distance, 0)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
