import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname+'.md')).read()

setup(
    name = "warc_diff_tools",
    version = "0.0.1",
    author = "Anastasia Aizman",
    author_email = "anastasia.aizman@gmail.com",
    description = ("WARC diff"),
    license = "BSD",
    keywords = "WARC diff",
    url = "",
    packages=['warc_compare', 'tests'],
    long_description=read('README'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
)
