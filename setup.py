#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='wordprofile',
      version='0.1.0',
      description='DWDS Wordprofile Server',
      author='René Knaebel',
      author_email='rene.knaebel@bbaw.de',
      packages=find_packages(),
      extra_requires={
          'parser': [
              'imsnpars @ git+https://github.com/zentrum-lexikographie/IMSnPars@0.1.0.2020080615'
          ]
      },
      install_requires=[
          'pymysql',
          'sqlalchemy',
          'termcolor',
          'tabulate',
          'fastapi',
          'uvicorn',
          'gunicorn'
      ],
      entry_points={
          'console_scripts': [
              'wp-init = wordprofile.cli.make_wp:main',
              'wp-parse = wordprofile.cli.parse_doc:main',
              'wp-xmlrpc = wordprofile.apps.xmlrpc_api:main',
              'wp-rest = wordprofile.apps.rest_api:main',
              'wp-vis = wordprofile.cli.vis:main',
          ],
      }
      )
