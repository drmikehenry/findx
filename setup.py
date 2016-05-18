#!/usr/bin/env python

from setuptools import setup, find_packages
import os

NAME = 'findx'


def open_file(name):
    return open(os.path.join(os.path.dirname(__file__), name))


__version__ = None
for line in open_file(NAME + '.py'):
    if line.startswith('__version__'):
        exec(line)
        break

setup(
    name=NAME,
    version=__version__,
    packages=find_packages(),
    py_modules=[NAME],
    entry_points={
        'console_scripts': [
            'findx=findx:main',
            'ffx=findx:ffx',
            'ffg=findx:ffg',
        ],
    },
    description='``findx``, an extended ``find`` command.',
    long_description=open_file('README.rst').read(),
    keywords='extended find file search',
    url='https://github.com/drmikehenry/findx',
    author='Michael Henry',
    author_email='drmikehenry@drmikehenry.com',
    license='MIT',
    zip_safe=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Topic :: Text Processing',
        'Topic :: Utilities',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
)
