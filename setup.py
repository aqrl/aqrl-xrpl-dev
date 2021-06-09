# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='aqrl-xrpl-dev',
    version='0.1.0',
    description='Aquarelle Finance XRPL Development Library',
    long_description=readme,
    author='Aquarelle Finance',
    author_email='aquarelle.finance@gmail.com',
    url='https://github.com/aqrl/aqrl-xrpl-dev',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
`
