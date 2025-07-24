# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI backend for the WAVE lab with PostgreSQL database support. The project uses:
- FastAPI for the web framework
- PostgreSQL for database (with separate dev/test instances)
- SQLAlchemy with asyncio for database ORM
- uv for dependency management
- Docker/Podman for containerized database services

### Documentation

After API changes, update `docs/api-usage.md` to keep documentation up to date.

After db schema changes, update `docs/database-schema.md` to keep documentation up to date.

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

## Authentication System

### Overview
The WAVE backend implements API key authentication with role-based access control using the Unkey service. This system validates Bearer tokens, extracts user roles, and enforces hierarchical permissions on FastAPI routes.

### Components
- **Role System** (`src/wave_backend/auth/roles.py`): Integer-based hierarchy (1=experimentee, 2=researcher, 3=test, 4=admin)
- **Unkey Client** (`src/wave_backend/auth/unkey_client.py`): REST client with Pydantic models for API validation
- **Auth Decorators** (`src/wave_backend/auth/decorator.py`): FastAPI dependencies for route protection

### Usage
```python
from wave_backend.auth.decorator import require_role, validate_api_key
from wave_backend.auth.roles import Role

# Basic key validation (any valid key)
@app.get("/protected")
async def protected_endpoint(auth: tuple = Depends(validate_api_key)):
    key_id, user_role = auth
    return {"access": "granted", "role": user_role}

# Role-based access control
@app.get("/researcher-only")
async def researcher_endpoint(auth: tuple = Depends(require_role(Role.RESEARCHER))):
    key_id, user_role = auth
    return {"data": "researcher level content"}
```

### Configuration
Required environment variables:
- `WAVE_API_KEY`: Unkey root API key for validation
- `WAVE_APP_ID`: Unkey application ID

### Data Flow
1. Client sends `Authorization: Bearer sk_abc123` header
2. FastAPI dependency extracts token, calls Unkey API with httpx
3. Unkey validates key and returns role/permissions information
4. System checks if user's role meets minimum requirement (hierarchical: admin ≥ test ≥ researcher ≥ experimentee)
5. Route executes if authorized, returns 401/403 if not

### Remaining Development Tasks
1. **Add httpx dependency** to pyproject.toml for HTTP client
2. **Create comprehensive large tests** with mocked Unkey API responses
3. **Update CI/CD** with WAVE_API_KEY and WAVE_APP_ID GitHub secrets
4. **Integration testing** with actual routes to verify complete auth flow

**IMPORTANT**: Role names and hierarchy must exactly match Unkey application configuration. Changes require synchronization between both systems.