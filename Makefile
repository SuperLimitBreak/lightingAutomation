ENV=_env
PYTHON_VERSION:=3
DEPENDENCIES_PYTHON:=requirements.txt
PYTHON:=$(ENV)/bin/python$(PYTHON_VERSION)
PIP:=$(ENV)/bin/pip$(PYTHON_VERSION)
PYTEST:=$(ENV)/bin/py.test

CONFIG_DEVELOPMENT=config.development.yaml
CONFIG_PRODUCTION=config.production.yaml
CONFIG_DIST=config.dist.yaml

help:
	#
	# stageOrchestration - Triggerable timed stage lighting + projector orchistration
	#  - install                :
	#    - upgrade_pip          : Update python dependencys
	#  - run                    : Run in development mode
	#    - run_production       : Braudcast to Artnet3
	#  - test                   : Run unit tests
	#


# Install ----------------------------------------------------------------------

.PHONY: install dependencys
dependencys: $(ENV)
install: dependencys upgrade_pip test

$(ENV):
	virtualenv --no-site-packages -p python$(PYTHON_VERSION) $(ENV)

$(CONFIG_DEVELOPMENT):
	cp $(CONFIG_DIST) $@
#$(CONFIG_PRODUCTION):
#	cp $(CONFIG_DIST) $@

../libs/:
	git clone https://github.com/calaldees/libs.git
../config-merger/:
	git clone https://github.com/calaldees/config-merger.git
../multisocketServer/:
	git clone https://github.com/SuperLimitBreak/multisocketServer.git
.PHONY: link_local_libs
link_local_libs: $(ENV) ../libs/ ../config-merger/ ../multisocketServer/
	$(PIP) install -e ../libs/
	$(PIP) install -e ../config-merger/
	$(PIP) install -e ../multisocketServer/


# Python Dependencys -----------------------------------------------------------

.PHONY: upgrade_pip
upgrade_pip:
	$(PIP) install --upgrade pip ; $(PIP) install --upgrade -r $(DEPENDENCIES_PYTHON)

# Build ------------------------------------------------------------------------

.PHONY: build
build:
	docker build --tag superlimitbreak/stageorchestration:latest .
.PHONY: push
push:
	docker push superlimitbreak/stageorchestration:latest


# Run --------------------------------------------------------------------------

.PHONY: run run_production

run: $(CONFIG_DEVELOPMENT)
	$(PYTHON) server.py --config $(CONFIG_DEVELOPMENT)

run_production: $(CONFIG_PRODUCTION)
	$(PYTHON) server.py --config $(CONFIG_PRODUCTION)


# Tests ------------------------------------------------------------------------

.PHONY: test
test:
	$(PYTEST) --doctest-modules

.PHONY: cloc
cloc:
	cloc --vcs=git


# Clean ------------------------------------------------------------------------

clean_cache:
	find . -iname *.pyc -delete
	find . -iname __pycache__ -delete
	find . -iname .cache -delete

clean: clean_cache
	rm -rf $(ENV)
	#rm -rf $(CONFIG_DEVELOPMENT)
