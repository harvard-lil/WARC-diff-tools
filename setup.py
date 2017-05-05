import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname+'.md')).read()

setup(
    name = "warc_diff_tools",
    version = "0.0.1",
    author = "Anastasia Aizman",
    author_email = "anastasia.aizman@gmail.com",
    description = ("WARC diff tools"),
    license = "BSD",
    keywords = "WARC diff",
    url = "",
    py_modules=["warc_compare"],
    long_description=read('README'),
)
