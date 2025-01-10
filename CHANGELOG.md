# Changelog

## [9.1.0](https://github.com/zentrum-lexikographie/wordprofile/compare/v9.0.0...v9.1.0) (2025-01-10)


### Features

* **Database:** Aggregate SQLAlchemy-based DB management in wordprofile.db ([990fd3f](https://github.com/zentrum-lexikographie/wordprofile/commit/990fd3f62a749c981f626e02aadc2b2f6b14a9b5))


### Bug Fixes

* **Database:** Remove unused `corpus_file_freqs`, impeding dumps ([282e82e](https://github.com/zentrum-lexikographie/wordprofile/commit/282e82e58671bc18a469e8fc15d9597585e8cccb))
* **preprocessing:** Instruct spacy to use gpu if available ([3d21d68](https://github.com/zentrum-lexikographie/wordprofile/commit/3d21d68c81c200832281f43b425b4bb1903933f3))
* **Project:** Migrates from pipenv to pip/pyproject.toml ([6895f7b](https://github.com/zentrum-lexikographie/wordprofile/commit/6895f7b7e590a54cf7daffd07a4d6952ede8306f))

## 9.0.0 (2024-12-17)


### Features

* **Continuous Integration:** Adds push of Docker images to internal registry ([a5bde89](https://github.com/zentrum-lexikographie/wordprofile/commit/a5bde8949065bcfac1b5c585deca13239631baf5))


### Miscellaneous Chores

* **Release:** Remove obsolete release script ([f36904f](https://github.com/zentrum-lexikographie/wordprofile/commit/f36904f2445487e89866d01a3d76bc376d3d8ed4))
