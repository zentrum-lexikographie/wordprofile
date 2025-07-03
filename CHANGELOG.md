# Changelog

## [9.1.0](https://github.com/zentrum-lexikographie/wordprofile/compare/v9.0.0...v9.1.0) (2025-07-03)


### Features

* **Database:** Aggregate SQLAlchemy-based DB management in wordprofile.db ([990fd3f](https://github.com/zentrum-lexikographie/wordprofile/commit/990fd3f62a749c981f626e02aadc2b2f6b14a9b5))


### Bug Fixes

* Add citation data ([47d76f4](https://github.com/zentrum-lexikographie/wordprofile/commit/47d76f492d44cf63b6e14c9105c22785479f9ae4))
* avoid retrieval of incorrect concordance for collocations ([#21](https://github.com/zentrum-lexikographie/wordprofile/issues/21)) ([880f7ef](https://github.com/zentrum-lexikographie/wordprofile/commit/880f7efd65e32a8416a0a4e23321ab58e4bd908a))
* **Database:** Remove unused `corpus_file_freqs`, impeding dumps ([282e82e](https://github.com/zentrum-lexikographie/wordprofile/commit/282e82e58671bc18a469e8fc15d9597585e8cccb))
* handle invalid ids ([7608d23](https://github.com/zentrum-lexikographie/wordprofile/commit/7608d239c852b11ef9de0287d87eeb06236bffe3))
* handle invalid ids for MWE ([ca97f0a](https://github.com/zentrum-lexikographie/wordprofile/commit/ca97f0a1d9ed9ffa6a33955d11c6085f2b079285))
* incorrect classification as 'OBJO' if token has 'Acc' case marking ([#22](https://github.com/zentrum-lexikographie/wordprofile/issues/22)) ([5b02751](https://github.com/zentrum-lexikographie/wordprofile/commit/5b02751eb0f7e1b5bc7e940b81214353b9a8b7f6))
* **preprocessing:** Instruct spacy to use gpu if available ([aed9fd8](https://github.com/zentrum-lexikographie/wordprofile/commit/aed9fd807e5dc72a31a70df7f17998a86b9cdcdf))
* **preprocessing:** Instruct spacy to use gpu if available ([3d21d68](https://github.com/zentrum-lexikographie/wordprofile/commit/3d21d68c81c200832281f43b425b4bb1903933f3))
* **Project:** Migrates from pipenv to pip/pyproject.toml ([6895f7b](https://github.com/zentrum-lexikographie/wordprofile/commit/6895f7b7e590a54cf7daffd07a4d6952ede8306f))
* use .txt instead of .in files for dependecies ([#19](https://github.com/zentrum-lexikographie/wordprofile/issues/19)) ([ce651b3](https://github.com/zentrum-lexikographie/wordprofile/commit/ce651b32759f7f9a3b3a2c5fef817d68c4371f68))


### Dependencies

* Prepare for release v9.1.0 ([08cc8e4](https://github.com/zentrum-lexikographie/wordprofile/commit/08cc8e4a8079e20b8094110d3f0a8b74481faf14))


### Documentation

* update docstrings ([80c25e7](https://github.com/zentrum-lexikographie/wordprofile/commit/80c25e7dad837922114fb5691dbdb43104a20d8e))

## 9.0.0 (2024-12-17)


### Features

* **Continuous Integration:** Adds push of Docker images to internal registry ([a5bde89](https://github.com/zentrum-lexikographie/wordprofile/commit/a5bde8949065bcfac1b5c585deca13239631baf5))


### Miscellaneous Chores

* **Release:** Remove obsolete release script ([f36904f](https://github.com/zentrum-lexikographie/wordprofile/commit/f36904f2445487e89866d01a3d76bc376d3d8ed4))
