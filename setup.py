#!/usr/bin/env python

import os
from setuptools import setup, find_packages

NAME = "findx"
for line in open(NAME + ".py"):
    if line.startswith("__VERSION__"):
        exec line in globals()
        break

setup(
        name=NAME,
        version=__VERSION__,
        description="""Extended ``find`` command""",
        packages=find_packages(),
        scripts=["findx.py"],
        entry_points={
            'console_scripts': [
                'findx = findx:main',
                'ffx = findx:ffx',
                'ffg = findx:ffg',
                ],
            },
        test_suite = 'nose.collector',
        author = 'Michael Henry',
        author_email = 'drmikehenry@drmikehenry.com',
        url = 'http://drmikehenry.com/',
        zip_safe = False
        )
