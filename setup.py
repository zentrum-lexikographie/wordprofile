#!/usr/bin/env python

from setuptools import setup, find_packages


setup(name='wordprofile',
      version='1.0.0',
      description='DWDS Wordprofile Server',
      author='René Knaebel',
      author_email='rene.knaebel@bbaw.de',
      packages=find_packages(),
      install_requires=[
          'pymysql',
          'sqlalchemy',
          'termcolor',
          'tabulate',
          'conllu',
      ],
      extras_require={
          'dev': [
              'autoflake',
              'flake8',
              'pytest'
          ]
      },
      entry_points={
          'console_scripts': [
              'wp-xmlrpc = apps.xmlrpc_api:main',
              'wp-rest = apps.rest_api:main',
          ],
      }
      )
