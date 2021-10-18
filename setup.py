#!/usr/bin/env python

from distutils.core import setup

setup(name='wordprofile',
      version='0.1.0',
      description='DWDS Wordprofile Server',
      author='René Knaebel',
      author_email='rene.knaebel@bbaw.de',
      packages=['wordprofile'],
      install_requires=[
          'pymysql',
          'sqlalchemy',
          'termcolor',
          'tabulate',
          'pytabs @ git+ssh://git@git.zdl.org/zdl/pytabs',
      ],
      entry_points={
          'console_scripts': [
              'wp-xmlrpc = apps.xmlrpc_api:main',
              'wp-rest = apps.rest_api:main',
          ],
      }
      )
