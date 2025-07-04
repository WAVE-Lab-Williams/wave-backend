# WAVE Backend

FastAPI backend for the WAVE lab with PostgreSQL database support.

## Repository Overview

The WAVE Backend is a comprehensive REST API designed for managing psychology and behavioral experiments. It provides a flexible, scalable platform for researchers to define experiment types, collect data, and perform advanced searches across experimental datasets.

### 🏗️ Architecture

**Tech Stack:**
- **FastAPI** - Modern, high-performance web framework for building APIs
- **PostgreSQL** - Robust relational database with asyncio support
- **SQLAlchemy** - Async ORM for database operations
- **Pydantic** - Data validation and settings management
- **uv** - Fast Python package manager
- **Docker/Podman** - Containerized database services

### 🚀 Quick Start

The fastest way to get started (assuming you have satisfied the requirements in [Prequisites](#prerequisites)) 
is with the all-in-one development command:

```bash
make setup-local-dev  # Initial setup
make dev              # Start database + API server
```

Then visit:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **API Documentation**: [docs/api-usage.md](docs/api-usage.md)
- **Database schema**: [docs/database-schema.md]

### 🧪 Development Workflow

**Standard Development:**
1. `make dev` - Start development environment
2. Make code changes
3. `make test-medium` - Run integration tests
4. `make format` - Format and lint code
5. `make shutdown` - Clean shutdown when done

**Database Management:**
- Development DB runs on port 5432
- Test DB runs on port 5433 (auto-started for tests)
- Both databases are completely isolated
- Reset commands available for clean testing

### 📊 API Capabilities

**Core Endpoints:**
- `/api/v1/experiment-types/` - Define experiment schemas
- `/api/v1/tags/` - Manage categorization tags  
- `/api/v1/experiments/` - Create and manage experiments
- `/api/v1/experiment-data/` - Collect and query experimental data
- `/api/v1/search/` - Advanced search and discovery

**Data Flow:**
1. **Define** experiment type with custom schema
2. **Create** experiment instance with metadata
3. **Collect** data using dynamic schema validation
4. **Search** and analyze across experiments
5. **Export** results for statistical analysis

## Development Environment

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

### 📁 Project Structure

```
src/wave_backend/
├── api/                    # FastAPI application and routes
│   ├── main.py            # FastAPI app setup and configuration
│   └── routes/            # API endpoint definitions
│       ├── experiments.py      # Experiment management
│       ├── experiment_data.py  # Dynamic data operations
│       ├── experiment_types.py # Experiment type definitions
│       ├── search.py           # Advanced search capabilities
│       └── tags.py             # Tag management
├── models/                # Database models and configuration
│   ├── database.py        # Database connection and sessions
│   └── models.py          # SQLAlchemy ORM models
├── schemas/               # Pydantic request/response models
│   ├── schemas.py         # Core data schemas
│   ├── search_schemas.py  # Search-specific schemas
│   └── column_types.py    # Database column type mappings
├── services/              # Business logic layer
│   ├── experiments.py         # Experiment operations
│   ├── experiment_data.py     # Dynamic table management
│   ├── experiment_types.py    # Experiment type operations
│   ├── search.py              # Advanced search service
│   └── tags.py                # Tag operations
└── utils/                 # Utility modules
    └── logging.py         # Centralized logging configuration

tests/
├── small/                 # Unit tests (no database)
├── medium/                # Integration tests (with database)
│   └── e2e/              # End-to-end workflow tests
└── large/                 # Performance and load tests

docs/
└── api-usage.md          # Comprehensive API documentation
```



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

