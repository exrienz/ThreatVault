# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ThreatVault is a next-generation unified vulnerability and compliance management platform that centralizes security operations. It transforms raw vulnerability data from multiple sources (Nessus, OpenVAS, OWASP ZAP, Trivy, etc.) into actionable intelligence through smart deduplication, SLA tracking, and AI-powered explanations.

## Development Commands

### Local Development

```bash
# Start PostgreSQL database for development
make dev_db

# Run FastAPI development server
make dev
```

### Docker Deployment

```bash
# Configure environment
cp .env.docker .env

# Launch with Docker Compose
docker-compose up --build -d

# View logs
docker-compose logs -f app

# Check status
docker-compose ps
```

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src tests/
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Code Quality

```bash
# Lint with ruff
ruff check src/

# Format code
ruff format src/
```

## Architecture

ThreatVault follows a **layered architecture** with clear separation of concerns:

### 1. Presentation Layer (`src/presentation/`)
- **HTML routes** (`src/presentation/html/v1/`) - Server-side rendered pages using Jinja2 templates
- **API routes** (`src/presentation/api/v1/`) - RESTful API endpoints
- Templates are located in `src/presentation/html/templates/`
- Uses HTMX 2.0.4 for dynamic UI updates and Server-Sent Events (SSE)

### 2. Application Layer (`src/application/`)
- **Services** (`src/application/services/`) - Business logic implementation
  - `finding_services.py` - Core vulnerability/compliance finding management
  - `plugin_services.py` - Plugin processing and verification
  - `auth_services.py` - Authentication and authorization
  - `cve_services.py` - CVE data retrieval and processing
- **Schemas** (`src/application/schemas/`) - Pydantic models for validation
- **Middlewares** (`src/application/middlewares/`) - Custom middleware components
- **Security** (`src/application/security/`) - Security utilities (JWT, OAuth2)
- **Utils** (`src/application/utils/`) - Helper functions and utilities
  - `startup.py` - Database initialization and seeding
  - `scheduler.py` - Background job scheduler
  - `plugin.py` - Plugin discovery and loading

### 3. Domain Layer (`src/domain/`)
- **Entities** (`src/domain/entity/`) - SQLAlchemy ORM models defining database schema
- **Constants** (`src/domain/constant.py`) - Enums and domain-specific constants
  - `SeverityEnum` - CRITICAL, HIGH, MEDIUM, LOW
  - `VAStatusEnum` - NEW, OPEN, CLOSED, EXEMPTION, OTHERS
  - `HAStatusEnum` - PASSED, FAILED, WARNING

### 4. Persistence Layer (`src/persistence/`)
- Database repository pattern implementations
- Each file corresponds to a database table/entity
- Handles direct database operations via SQLAlchemy

### 5. Infrastructure Layer (`src/infrastructure/`)
- **Database** (`src/infrastructure/database/`) - Database connection and session management
- **Services** (`src/infrastructure/services/`) - External service integrations (OpenAI, etc.)

## Plugin System

ThreatVault uses a **flexible plugin architecture** for parsing vulnerability and compliance scan data:

### Plugin Types
- **VA (Vulnerability Assessment)** - `plugins/*/va/` - Process vulnerability scan data
- **HA (Host Assessment/Compliance)** - `plugins/*/ha/` - Process compliance/configuration data

### Plugin Locations
- `plugins/builtin/` - Built-in plugins shipped with ThreatVault
- `plugins/custom/` - Custom user-created plugins

### Plugin Structure
Each plugin must implement a `process(data: bytes) -> pl.LazyFrame | pl.DataFrame | pd.DataFrame` function that:
1. Accepts raw file data as bytes
2. Returns a DataFrame/LazyFrame with the required schema (see `plugins/PLUGIN_DEVELOPMENT.md`)
3. Handles data transformation and normalization

**Important**: Plugins are auto-discovered at startup via `src/application/utils/startup.py:upload_builtin_plugin()`

## Data Processing

ThreatVault heavily uses **Polars** for efficient data processing:
- Findings are processed as `pl.LazyFrame` for lazy evaluation
- Large CSV files are handled with minimal memory footprint
- Data transformations occur before database persistence

## Key Workflows

### Finding Upload Flow
1. User uploads scan file via web UI
2. Plugin identified by scanner type (VA/HA)
3. Plugin's `process()` function transforms CSV to DataFrame
4. Schema verification ensures correct columns/types
5. Deduplication logic identifies existing findings
6. New findings saved to database with SLA timestamps
7. Real-time updates pushed via Server-Sent Events (SSE)

### Authentication & Authorization
- JWT tokens for API authentication (`src/application/security/`)
- Role-Based Access Control (RBAC) with 5 default roles:
  - Administrator - Full system control
  - ITSE (IT Security Engineer) - Security operations
  - Management - Read-only strategic oversight
  - Product Owner - Product-specific access
  - Audit - Compliance oversight (under development)
- Permissions defined in `src/default/permissions.json`
- Role-permission mappings in `src/default/role_permission.json`

### Database Initialization
On startup (`src/application/utils/startup.py`):
1. Creates database if not exists
2. Runs Alembic migrations
3. Seeds default roles and permissions
4. Loads builtin plugins
5. Creates default global SLA configuration
6. Starts scheduler for background jobs

## Technology Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL 17.0 with SQLAlchemy (async ORM)
- **Data Processing**: Polars (primary), Pandas (compatibility)
- **Frontend**: Server-side templates (Jinja2) + HTMX 2.0.4 + jQuery + Bootstrap
- **Authentication**: JWT + OAuth2
- **Migrations**: Alembic
- **Testing**: pytest with pytest-asyncio

## Configuration

Configuration is managed via environment variables (`.env` file):
- `DB_URL` - PostgreSQL connection string
- `JWT_SECRET` - JWT signing secret
- `SESSION_SECRET_KEY` - Session middleware secret
- `HTTP_PROXY`/`HTTPS_PROXY` - Proxy settings for external requests

Default configurations stored in:
- `src/default/roles.json` - Default role definitions
- `src/default/permissions.json` - Permission scopes
- `src/default/role_permission.json` - Role-permission assignments
- `src/default/sidebars.json` - UI sidebar navigation

## Static Assets

- Static files served from `/assets` endpoint (mounted to `static/` directory)
- Public assets in `public/` directory
- Frontend dependencies managed via npm (`package.json`)

## Important Notes

- The internal application name is "Sentinel" (legacy), but product name is "ThreatVault"
- Always use async database operations where possible (`AsyncSession`)
- Findings are tracked at **host:port:CVE level** for granular SLA management
- SLA days are configurable per severity level in Global Config
- Plugin verification happens before processing uploads to ensure schema compliance
- Database schema changes require Alembic migrations - never modify tables directly
