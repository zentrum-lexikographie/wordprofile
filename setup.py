from setuptools import setup, find_packages

setup(name='wordprofile',
      version='1.0.0',
      description='DWDS Wordprofile Server',
      author='René Knaebel',
      author_email='rene.knaebel@bbaw.de',
      packages=find_packages(exclude=["tests"]),
      install_requires=[
          'pymysql',
          'sqlalchemy',
          'termcolor',
          'tabulate',
          'conllu',
          'fastapi',
          'uvicorn',
          'gunicorn',
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
              'wp-xmlrpc = wordprofile.apps.xmlrpc_api:main',
              'wp-rest = wordprofile.apps.rest_api:main',
          ],
      }
      )
