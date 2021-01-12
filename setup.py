#!/usr/bin/env python
# Install script for the sbxreader utilities.

import os
from os.path import join as pjoin
from setuptools import setup
from setuptools.command.install import install

with open("README.md", "r") as fh:
    longdescription = fh.read()

setup(
    name = 'sbxreader',
    version = '0.1.0',
    author = 'Joao Couto',
    author_email = 'jpcouto@gmail.com',
    description = (longdescription),
    long_description = longdescription,
    license = 'GPL',
    install_requires = requirements,
    url = "https://github.com/jcouto/sbxreader",
    packages = ['sbxreader'],
    entry_points = {
        'console_scripts': [
            'sbxviewer = sbxreader.viewer:main',
        ]
    },
)


