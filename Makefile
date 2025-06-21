###############################################################################
# MAIN CONFIGURATION
###############################################################################
.PHONY: clean format 

SOURCE_DIR=./src
SOURCE_PATH=./src/wave-backend
TESTS_DIR=./tests
PYTEST_LOG_LEVEL=DEBUG
PYTEST_COV_MIN=50

# Load all environment variables from .env
# so that they are preloaded before running any command here
ifneq (,$(wildcard ./.env))
include .env
export
endif

###############################################################################
# DOCKER CONFIGURATION
###############################################################################
# Docker/Podman configuration
DOCKER_CMD := $(strip $(shell command -v podman 2> /dev/null || echo docker))
DOCKER_CMD := $(notdir $(DOCKER_CMD))
# Check if using podman and adjust compose command accordingly
ifeq ($(DOCKER_CMD),podman)
	COMPOSE_CMD := $(DOCKER_CMD) compose
else
	COMPOSE_CMD := $(DOCKER_CMD)-compose
endif

# Podman specific settings
MACHINE_NAME := podman-machine-default
MACHINE_CPUS := 4
MACHINE_MEMORY := 4096

# Set the platform for the build
PLATFORM = linux/arm64
IMAGE_NAME := cvi/cvi-cust-model-inference
CONTAINER_NAME := sagemaker-inference
PORT := 8080

###############################################################################
# Housekeeping
###############################################################################
clean:
	find . -type f -name ".DS_Store" -exec rm -rf {} +
	find . -type f -name "*.py[cod]" -exec rm -rf {} +
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage*" -exec rm -f {} +

isort: 
	uv run isort .

black:
	uv run black .

flake8:
	uv run flake8

pylint:
	uv run pylint **/*.py

format: isort black flake8 pylint

###############################################################################
# Local Development
###############################################################################

setup-local-dev:
	@echo "Setting up local development environment..."
	@echo "Creating virtual environment..."
	uv venv
	uv pip install -e .[dev,test]
	@echo "Installing pre-commit hooks..."
	uv run pre-commit install
	@echo "Local development environment ready!"

# Add podman-check target to handle Podman machine initialization
podman-check:
ifeq "$(DOCKER_CMD)" "podman"
	@echo "Detected podman, checking machine status..."
	@if ! podman machine list | grep -q "$(MACHINE_NAME).*Running"; then \
		echo "Initializing and starting podman machine..."; \
		podman machine init --cpus $(MACHINE_CPUS) --memory $(MACHINE_MEMORY) $(MACHINE_NAME) || true; \
		podman machine start $(MACHINE_NAME) || true; \
		echo "Podman machine started"; \
	else \
		echo "Podman machine is already running"; \
	fi
endif

###############################################################################
# Sized testing
###############################################################################
define run_tests
	@mkdir -p logs
		uv run coverage run --data-file=logs/.coverage --source=${SOURCE_DIR} --omit="*/tests/*" \
		-m pytest -rs -vv --log-level=${PYTEST_LOG_LEVEL} $1 \
		> logs/pytest_output.log
endef

test-all:
	$(call run_tests,${TESTS_DIR},${PYTEST_COV_MIN})

test-small:
	$(call run_tests,${TESTS_DIR}/small)

test-medium:
	$(call run_tests,${TESTS_DIR}/medium)

test-large:
	$(call run_tests,${TESTS_DIR}/large)