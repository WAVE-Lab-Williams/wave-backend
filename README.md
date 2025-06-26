# WAVE Backend

FastAPI backend for the WAVE lab with PostgreSQL database support.

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for dependency management
- Docker or Podman for PostgreSQL

### Setup

1. **Set up the development environment:**
   ```bash
   make setup-local-dev
   ```

2. **Start the PostgreSQL development database:**
   ```bash
   make dev-db
   ```

3. **Start the FastAPI development server:**
   ```bash
   make serve
   ```

   Or start both database and server together:
   ```bash
   make dev
   ```

4. **Visit the application:**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

## Available Commands

### Development
- `make setup-local-dev` - Set up local development environment
- `make serve` - Start FastAPI development server
- `make dev` - Start database and server together
- `make dev-stop` - Stop development environment
- `make shutdown` - Complete shutdown (stops all services, databases, and containers)

**Note:** Use `make shutdown` when you want to completely stop all development services, including the FastAPI server, all databases, Docker/Podman containers, and (if using Podman) the Podman machine itself.

### Database Management
- `make dev-db` - Start development PostgreSQL database
- `make dev-db-stop` - Stop development database
- `make dev-db-logs` - Show database logs
- `make dev-db-reset` - Reset database (removes all data)

### Test Database
- `make test-db` - Start test PostgreSQL database
- `make test-db-stop` - Stop test database
- `make test-db-reset` - Reset test database (removes all data)

### Combined Database Management
- `make db-stop` - Stop both development and test databases
- `make db-reset` - Reset both databases (removes all data and restarts them)

### Docker/Podman Management
- `make docker-up` - Start all services with Docker Compose
- `make docker-down` - Stop all services with Docker Compose
- `make docker-logs` - Show logs for all services
- `make docker-status` - Show status of all services
- `make docker-shell-postgres` - Connect to PostgreSQL database shell
- `make docker-clean` - Clean unused Docker/Podman resources
- `make docker-deep-clean` - Deep clean ALL Docker/Podman resources (with confirmation)

### Testing
- `make test-small` - Run small tests (no database required)
- `make test-medium` - Run medium tests (automatically starts test database)
- `make test-large` - Run large tests
- `make test-all` - Run all tests (automatically starts test database)

**Note:** Medium and full test suites require the test database. The `test-medium` and `test-all` commands will automatically start the test PostgreSQL database on port 5433.

### Code Quality
- `make format` - Format code (isort, black, flake8, pylint)
- `make clean` - Clean up temporary files

## Configuration

The application uses environment variables for configuration. All PostgreSQL and FastAPI settings are loaded from the `.env` file (refer to `.env.examaple`)

### Environment Variables

Copy `.env.example` to `.env` and modify as needed:

```bash
cp .env.example .env
```

Key configuration variables:
- `POSTGRES_DB` - PostgreSQL database name (default: wave_dev)
- `POSTGRES_USER` - PostgreSQL username (default: wave_user)  
- `POSTGRES_PASSWORD` - PostgreSQL password (default: wave_password)
- `POSTGRES_PORT` - PostgreSQL port (default: 5432)
- `POSTGRES_TEST_PORT` - Test database port (default: 5433)
- `FASTAPI_HOST` - FastAPI host (default: 0.0.0.0)
- `FASTAPI_PORT` - FastAPI port (default: 8000)

