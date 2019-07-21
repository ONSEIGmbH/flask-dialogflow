# -*- coding: utf-8 -*-
#
# Copyright (c) ONSEI GmbH

from setuptools import setup, find_packages

from onsei_google import __version__

with open('README.md') as fp:
    long_description = fp.read()


setup(
    name='ONSEI_Google',
    version=__version__,
    packages=find_packages(),
    url='https://github.com/ONSEIGmbH/ONSEI_Google',
    python_requires='>3.6',
    license='Proprietary',
    author='ONSEI GmbH',
    author_email='georg@onsei.de',
    description='A helper library for Actions-on-Google/Dialogflow agents.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'dataclasses==0.6;python_version<"3.7"',
        'Flask==1.0.2',
        'marshmallow[reco]==3.0.0rc5',  # Marshmallow with recommended deps
        'marshmallow-enum==1.4.1',
        'PyYAML==5.1',
        'tabulate==0.8.3',
    ],
    entry_points={
        'flask.commands': [
            'agent=onsei_google.cli:agent_cli'
        ],
    },
)
