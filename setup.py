#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='Lib.fm',
    version='0.1',
    description='A Python library for the last.fm API',
    long_description="Lib.fm is a lightweight wrapper over the last.fm API.",
    author='MihaiDamian',
    author_email='',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)
