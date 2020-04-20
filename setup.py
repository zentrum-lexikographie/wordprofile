#!/usr/bin/env python

from distutils.core import setup

setup(name='wordprofile',
      version='0.0.1',
      description='DWDS Wordprofile Server',
      author='René Knaebel',
      author_email='rene.knaebel@bbaw.de',
      packages=['wordprofile'],
      install_requires=[
          'pymysql',
          'sqlalchemy',
          'imsnpars',
          'termcolor',
          'tabulate'
      ],
      entry_points={
          'console_scripts': [
              'wp-init = cli.make_wp:main',
              'wp-parse = cli.parse_doc:main',
              'wp-run = apps.rest_api:main'
          ],
      }
      )
