#! /usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

setup(
    name='OpenFisca-canada-csps',
    version='13.0.4',
    author='Government of Canada, Digital Technology Solutions - Solutions de technologies numériques',
    author_email='michael.bungay@hrsdc-rhdcc.gc.ca,tjharrop@gmail.com',
    description='OpenFisca tax and benefit system for Canada',
    keywords='benefit microsimulation social tax',
    license='AGPL-3.0-or-later',
    url='https://github.com/DTS-STN/openfisca-canada-dts-csps',
    include_package_data=True,
    install_requires=[
        'OpenFisca-Core[web-api]>=43,<44',
    ],
    extras_require={
        'dev': [
            'flake8>=6,<8',
            'pytest>=7,<9',
            'yamllint>=1.35,<2',
        ],
    },
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'mvohwr-ui=app.server:main',
        ],
    },
)
