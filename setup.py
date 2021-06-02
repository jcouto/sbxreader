#!/usr/bin/env python
# Install script for the sbxreader utilities.

import os
from os.path import join as pjoin
from setuptools import setup
from setuptools.command.install import install


#
longdescription = """

# sbxreader

Python module to read Neurolabware Scanbox files.

Check the git repository for [examples](https://github.com/jcouto/sbxreader.git).
 ``pip install sbxreader``

Source code is in [the repository](https://github.com/jcouto/sbxreader.git)

"""

setup(
    name = 'sbxreader',
    version = '0.1.6a',
    author = 'Joao Couto',
    author_email = 'jpcouto@gmail.com',
    description = "Python module to read Neurolabware Scanbox files.",
    long_description = longdescription,
    long_description_content_type='text/markdown',
    license = 'GPL',
    install_requires = ['scipy'],
    url = "https://github.com/jcouto/sbxreader",
    packages = ['sbxreader'],
    entry_points = {
        'console_scripts': [
            'sbxviewer = sbxreader.viewer:main',
        ]
    },
)


