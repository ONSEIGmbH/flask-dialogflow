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
        'dataclasses==0.6.0;python_version<"3.9"',
        'Flask==1.0.2',
        'marshmallow_enum @ git+https://github.com/big-picture/marshmallow_enum.git@master#egg=marshmallow_enum',
        'PyYAML==5.1',
        'tabulate==0.8.3',
    ],
    entry_points={
        'flask.commands': [
            'agent=flask_dialogflow.cli:agent_cli'
        ],
    },
)
