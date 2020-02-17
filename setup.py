#!/usr/bin/env python
# coding=utf-8

import setuptools
import sys
try:
    from typing import Any, IO
except ImportError:
    pass

sys_version = tuple(sys.version_info[:2])
min_version = (2, 6)
if sys_version < min_version:
    sys.exit(
        "Python version %d.%d is too old; %d.%d or newer is required."
        % (sys_version + min_version)
    )


def open_text(name):
    # type: (str) -> IO[Any]
    if sys_version[0] == 2:
        return open(name)
    return open(name, encoding="utf-8")


NAME = "findx"

__version__ = None
for line in open_text("src/" + NAME + ".py"):
    if line.startswith("__version__"):
        __version__ = line.split('"')[1]
        break

with open_text("README.rst") as f:
    long_description = f.read()

with open_text("requirements.txt") as f:
    requirements = f.read()

with open_text("dev-requirements.txt") as f:
    dev_requirements = f.read()

setuptools.setup(
    name=NAME,
    version=__version__,
    packages=setuptools.find_packages("src"),
    package_dir={"": "src"},
    py_modules=[NAME],
    python_requires=">=2.6,!=3.0.*,!=3.1.*,!=3.2.*",
    install_requires=requirements,
    extras_require={"dev": dev_requirements},
    entry_points={
        "console_scripts": [
            "findx=findx:main",
            "ffx=findx:ffx",
            "ffg=findx:ffg",
        ],
    },
    include_package_data=True,
    description="``findx``, an extended ``find`` command.",
    long_description=long_description,
    keywords="extended find file search",
    url="https://github.com/drmikehenry/findx",
    author="Michael Henry",
    author_email="drmikehenry@drmikehenry.com",
    license="MIT",
    zip_safe=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Text Processing",
        "Topic :: Utilities",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
