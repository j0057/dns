#!/usr/bin/env python2.7

repo_names = ['xmlist', 'xhttp']
dist_names = ['pygraphviz']
static_dirs = ['conf']

import setuptools
import os

try:
    with open('dns.egg-info/version.txt') as f: 
        version = f.read()
except:
    version = None

setuptools.setup(
    author='Joost Molenaar',
    author_email='j.j.molenaar@gmail.com',
    url='https://github.com/j0057/dns',
    name='dns',
    version=version,
    version_command=('git describe', 'pep440-git'),
    packages=['dns'],
    data_files=[ (root, [ root + '/' + f for f in files ])
                 for src_dir in static_dirs
                 for (root, dirs, files) in os.walk(src_dir) ],
    install_requires=dist_names + repo_names,
    custom_metadata={
        'x_repo_names': repo_names,
        'x_dist_names': dist_names,
        'x_static_dirs': static_dirs
    }
)
