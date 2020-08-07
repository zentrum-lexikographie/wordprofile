default: docker_build

.PHONY: dev-setup
dev-setup:
	@pip install -r requirements-dev.txt


.PHONY: test
test:
	@pytest

.PHONY: docker_build
docker_build: VERSION = $(shell git describe --tags --always)
docker_build:
	@docker build \
		--build-arg BUILD_DATE=`date -u +"%Y-%m-%dT%H:%M:%SZ"` \
		--build-arg VCS_REF=`git rev-parse --short HEAD` \
		--build-arg VERSION=$(VERSION) \
		-t lex.dwds.de/zdl-wordprofile:$(VERSION) .
