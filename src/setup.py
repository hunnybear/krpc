#!/usr/bin/env python

import setuptools

name = 'ozzybear_krpc'


setuptools.setup(
    name=name,
    version='0.1',
    author="Matt Oztalay and Tyler Jachetta",
    author_email="me@tylerjachetta.net",
    url="www.hemaalliance.com",
    description="the dumb name is Tyler's fault",
    long_description="todo",
    requires=['krpc'],
    license="MIT License",
    packages=setuptools.find_packages(),
    data_files=[],
    entry_points = {
        'console_scripts': [
            'hello_world=ozzybear_krpc.cli.cli_experiments:hello_world',
            'launch_test=ozzybear_krpc.cli.cli_experiments:launch_tests',
            'orbit_test=ozzybear_krpc.cli.cli_experiments.orbit_test'
        ],
    }
)
