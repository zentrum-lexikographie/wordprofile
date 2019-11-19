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
              'wp-init = init_database:main',
              'wp-create = create_database:main',
              'wp-parse = parse_doc:main',
              'wp-run = run_server:main'
          ],
      }
      )
