DOCKER_BASE ?= camptocamp/geomapfish
MAJOR_VERSION ?= 2.4

.PHONY: prepare-tests  # local target for development purpose
prepare-tests:
	cd ../.. && ./docker-run make docker-build-testdb
	cd ../.. && ./docker-run docker build \
		--build-arg=VERSION=3.4 \
		--tag=$(DOCKER_BASE)-qgisserver:gmf$(MAJOR_VERSION)-qgis3.4 \
		docker/qgisserver
	cd ../.. && ./docker-run make docker/qgisserver/acceptance_tests/geomapfish.yaml

.PHONY: tests
tests:
	docker-compose -f acceptance_tests/docker-compose.yaml build qgisserver-tests
	docker-compose -f acceptance_tests/docker-compose.yaml run --rm qgisserver-tests

.PHONY: clean
clean:
	find . -type d -name __pycache__ | xargs rm -rf
	find . -type d -name .pytest_cache | xargs rm -rf
