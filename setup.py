# -*- coding: utf-8 -*-
#
# Copyright (c) ONSEI GmbH

from setuptools import setup, find_packages

from flask_dialogflow import __version__

with open('README.md') as fp:
    long_description = fp.read()


setup(
    name='flask-dialogflow',
    version=__version__,
    packages=find_packages(),
    url='https://github.com/ONSEIGmbH/flask-ONSEI',
    python_requires='>3.6',
    license='APACHE LICENSE, VERSION 2.0',
    author='ONSEI GmbH',
    author_email='it@onsei.de',
    description='A helper library for Actions-on-Google/Dialogflow agents.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'dataclasses==0.6;python_version<"3.7"',
        'Flask==1.1.1',
        'marshmallow[reco]==3.0.0rc5',  # Marshmallow with recommended deps
        'marshmallow-enum==1.4.1',
        'PyYAML==5.1',
        'tabulate==0.8.3',
    ],
    entry_points={
        'flask.commands': [
            'agent=flask_dialogflow.cli:agent_cli'
        ],
    },
)
