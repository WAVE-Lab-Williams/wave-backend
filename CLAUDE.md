# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI backend for the WAVE lab with PostgreSQL database support. The project uses:
- FastAPI for the web framework
- PostgreSQL for database (with separate dev/test instances)
- SQLAlchemy with asyncio for database ORM
- uv for dependency management
- Docker/Podman for containerized database services

## Essential Commands

### Development Setup
```bash
make setup-local-dev    # Initial setup: creates venv, installs deps, sets up pre-commit
make dev               # Start database and FastAPI server together
make serve             # Start just the FastAPI server (assumes DB is running)
make shutdown          # Complete shutdown: stops all services, databases, containers
```

**Important**: The `shutdown` command provides a comprehensive cleanup that stops:
- FastAPI development server (uvicorn process)
- All Docker/Podman containers (dev + test databases)  
- Podman machine (if using Podman)

Use this when you want to completely clean up the development environment.

### Database Management
```bash
make dev-db            # Start development PostgreSQL (port 5432)
make test-db           # Start test PostgreSQL (port 5433)
make dev-db-reset      # Reset dev database (removes all data)
make test-db-reset     # Reset test database (removes all data)
make db-reset          # Reset both databases (removes all data)
make db-stop           # Stop both databases
```

### Testing
```bash
make test-small        # Run small/unit tests (no database required)
make test-medium       # Run medium/integration tests (auto-starts test DB)
make test-large        # Run large/end-to-end tests
make test-all          # Run all test suites (auto-starts test DB)
```

**Important**: Medium and full test suites require the test database (PostgreSQL on port 5433). 
The `test-medium` and `test-all` commands automatically start the test database as a dependency.

WARNING: `make test-*` commands save to `logs/pytest_output.log`, which can be verbose. You are better
off directly running `uv run pytest ...` with correct arguments

### Code Quality
```bash
make format            # Run isort, black, flake8, pylint
```

## Architecture

### Project Structure
- `src/wave_backend/` - Main application package
- `src/wave_backend/api/main.py` - FastAPI application entry point
- `src/wave_backend/utils/` - Shared utilities (logging, constants)
- `tests/` - Test suites organized by size (small/medium/large)

### Key Components
- **FastAPI App**: Configured with lifespan events, accessible at http://localhost:8000
- **Database**: PostgreSQL with separate dev/test instances using Docker Compose
- **Logging**: Centralized logging configuration via `logging_config.ini`
- **Environment**: Configuration via `.env` file (copy from `.env.example`)

### Development Workflow
1. Use `make setup-local-dev` for initial setup
2. Use `make dev` to start both database and API server
3. API docs available at http://localhost:8000/docs
4. Test database runs on port 5433 to avoid conflicts

### Docker/Podman Support
The project auto-detects Docker vs Podman and adjusts commands accordingly. Podman users get automatic machine management.

### Testing Strategy
Tests are organized by size/scope:
- **Small**: Unit tests, fast execution, no external dependencies
- **Medium**: Integration tests with database dependencies (uses test DB on port 5433)
- **Large**: End-to-end tests, full system testing

The medium and full test suites require a test database which runs in a separate PostgreSQL container
on port 5433 to avoid conflicts with the development database (port 5432).

All tests use pytest with asyncio support and coverage reporting.