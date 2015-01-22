#!/usr/bin/env python2.7

repo_names = ['xmlist', 'xhttp']
dist_names = ['pygraphviz']
static_dirs = ['conf']

from setuptools import setup
import os

setup(
    author='Joost Molenaar',
    author_email='j.j.molenaar@gmail.com',
    url='https://github.com/j0057/dns',
    name='dns',
    version_command='git describe',
    version_command_pep440='git-dev',
    packages=['dns'],
    data_files=[ (root, map(lambda f: root + '/' + f, files))
                 for src_dir in static_dirs
                 for (root, dirs, files) in os.walk(src_dir) ],
    install_requires=dist_names + repo_names,
    custom_metadata={
        'x_repo_names': repo_names,
        'x_dist_names': dist_names,
        'x_static_dirs': static_dirs
    }
)
