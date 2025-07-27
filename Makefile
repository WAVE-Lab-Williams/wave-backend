###############################################################################
# MAIN CONFIGURATION
###############################################################################
.PHONY: clean format

SOURCE_DIR=./src
SOURCE_PATH=./src/wave_backend
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
	@echo "Checking for .env file..."
	@if [ -f .env ]; then \
		echo "✓ .env file found - using existing configuration"; \
	else \
		cp .env.example .env; \
		echo "✓ .env file created from template, please edit it to configure your environment"; \
	fi
	@echo "Local development environment ready!"

# FastAPI Development Server
serve:
	@echo "Starting FastAPI development server..."
	uv run uvicorn wave_backend.api.main:app --host $(FASTAPI_HOST) --port $(FASTAPI_PORT) --reload

# Database Development Commands
dev-db: podman-check
	@echo "Starting development PostgreSQL database..."
	$(COMPOSE_CMD) up -d postgres

dev-db-stop:
	@echo "Stopping development PostgreSQL database..."
	$(COMPOSE_CMD) down

dev-db-logs:
	@echo "Showing PostgreSQL database logs..."
	$(COMPOSE_CMD) logs -f postgres

dev-db-reset: dev-db-stop
	@echo "Resetting development database (removing volumes)..."
	$(COMPOSE_CMD) down -v
	$(COMPOSE_CMD) up -d postgres

# Test Database Commands
test-db: podman-check
	@echo "Starting test PostgreSQL database..."
	$(COMPOSE_CMD) --profile test up -d postgres-test

test-db-stop:
	@echo "Stopping test PostgreSQL database..."
	$(COMPOSE_CMD) --profile test down

test-db-reset: test-db-stop
	@echo "Resetting test database (removing volumes)..."
	$(COMPOSE_CMD) --profile test down -v
	$(COMPOSE_CMD) --profile test up -d postgres-test

# Combined Database Commands
db-stop: dev-db-stop test-db-stop
	@echo "All databases stopped"

db-reset: dev-db-stop test-db-stop
	@echo "Resetting both development and test databases (removing volumes)..."
	$(COMPOSE_CMD) down -v
	$(COMPOSE_CMD) --profile test down -v
	@echo "Starting development database..."
	$(COMPOSE_CMD) up -d postgres
	@echo "Starting test database..."
	$(COMPOSE_CMD) --profile test up -d postgres-test
	@echo "Both databases reset and restarted"

# Combined Development Commands
dev: dev-db
	@echo "Starting full development environment..."
	@echo "Waiting for database to be ready..."
	@sleep 5
	@$(MAKE) serve

dev-stop: dev-db-stop
	@echo "Development environment stopped"

# Complete shutdown - stops everything
shutdown: 
	@echo "Shutting down all development services..."
	@echo "Stopping FastAPI server (if running)..."
	@pkill -f "uvicorn wave_backend.api.main:app" || true
	@echo "Stopping all Docker/Podman containers..."
	$(COMPOSE_CMD) down
	$(COMPOSE_CMD) --profile test down
	@echo "Stopping podman machine (if using podman)..."
ifeq "$(DOCKER_CMD)" "podman"
	@podman machine stop $(MACHINE_NAME) || true
endif
	@echo "Complete shutdown finished - all services stopped"

###############################################################################
# Docker Compose Commands
###############################################################################

# Start all services with Docker Compose
docker-up: podman-check
	$(COMPOSE_CMD) up -d
	@echo "All services started with Docker Compose"
	@echo "FastAPI: http://localhost:$(FASTAPI_PORT)"

# Stop all services with Docker Compose
docker-down: podman-check
	$(COMPOSE_CMD) down
	@echo "All services stopped with Docker Compose"

# Clean Docker/Podman resources (images, containers, etc.)
docker-clean: docker-down
	@echo "Cleaning Docker/Podman resources..."
	$(DOCKER_CMD) system prune -f
	@echo "Removed unused containers, networks, and dangling images"

# Deep clean all Docker/Podman resources including volumes
docker-deep-clean: docker-down
	@echo "WARNING: This will remove ALL Docker/Podman resources including volumes!"
	@echo "This operation cannot be undone."
	@read -p "Are you sure you want to continue? [y/N] " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		echo "Performing deep clean of Docker/Podman resources..."; \
		$(DOCKER_CMD) system prune -af --volumes; \
		if [ "$(DOCKER_CMD)" = "podman" ]; then \
			echo "Removing podman machine..."; \
			podman machine rm -f $(MACHINE_NAME) || true; \
			echo "Podman machine removed"; \
		fi; \
		echo "Deep clean completed"; \
	else \
		echo "Deep clean cancelled"; \
	fi

# Show logs for all services
docker-logs: podman-check
	$(COMPOSE_CMD) logs -f

# Show status of all services
docker-status: podman-check
	$(COMPOSE_CMD) ps

# Connect to the PostgreSQL container shell
docker-shell-postgres: podman-check
	$(DOCKER_CMD) exec -it wave-postgres-dev psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

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
		-m pytest -rs -vv --log-level=${PYTEST_LOG_LEVEL} $1 --durations 5 \
		> logs/pytest_output.log
endef

test-all: test-db
	@echo "Running all tests with test database..."
	$(call run_tests,${TESTS_DIR},${PYTEST_COV_MIN})

test-small:
	$(call run_tests,${TESTS_DIR}/small)

test-medium: test-db
	@echo "Running medium tests with test database..."
	$(call run_tests,${TESTS_DIR}/medium)

test-large:
	$(call run_tests,${TESTS_DIR}/large)
