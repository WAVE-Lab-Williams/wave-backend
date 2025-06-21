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

### Database Management
- `make dev-db` - Start development PostgreSQL database
- `make dev-db-stop` - Stop development database
- `make dev-db-logs` - Show database logs
- `make dev-db-reset` - Reset database (removes all data)

### Testing
- `make test-small` - Run small tests
- `make test-all` - Run all tests
- `make test-db` - Start test database
- `make test-db-stop` - Stop test database

### Code Quality
- `make format` - Format code (isort, black, flake8, pylint)
- `make clean` - Clean up temporary files

## Database and FastAPI Configuration

The PostgreSQL database and FastAPI endpoint are configured with environment variables,
see `.env.example`

### Environment Variables

Copy `.env.example` to `.env` and modify as needed:

```bash
cp .env.example .env
```

