#!/usr/bin/env python

from distutils.core import setup

setup(name='ghaminer',
      version='1.0',
      description='Miner tool for GHAM',
      author='Jan Sedlak',
      author_email='mail@jansedlak.cz',
      url='https://github.com/garretraziel/ghaminer',
      packages=['ghaminer'],
      install_requires=[
          'pause', 'numpy', 'githubpy', 'python-dateutil', 'pytz', 'pandas', 'scipy'
      ],
     )
