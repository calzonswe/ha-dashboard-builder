# HA Dashboard Builder

A modern Home Assistant dashboard builder that lets you visually design custom dashboards by dragging and dropping entities from your HA instance. Built with FastAPI backend and React frontend.

## Features

- **Visual Drag & Drop Interface**: Design dashboards intuitively by dragging entities onto canvas
- **Real-time Entity Discovery**: Automatically discover all Home Assistant entities (sensors, lights, switches, etc.)
- **Smart Grouping**: Entities grouped by area, device, or domain for easy navigation
- **State Change Tracking**: Monitor entity state changes with history tracking
- **SQLite Persistence**: Fast local caching of entity data with automatic refresh
- **REST API**: Complete RESTful API for dashboard management and entity operations
- **Docker Ready**: Easy deployment with Docker Compose

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   React     │◄──►│  FastAPI     │◄──►│ Home        │
│   Frontend  │    │  Backend     │    │ Assistant   │
└─────────────┘    └──────────────┘    └─────────────┘
                        │
                   ┌─────────┐
                   │ SQLite  │
                   │ Cache   │
                   └─────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Home Assistant instance with API access
- Docker (optional, for containerized deployment)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ha-dashboard-builder.git
cd ha-dashboard-builder

# Install dependencies
pip install -r backend/requirements.txt

# Run tests to verify setup
pytest backend/tests/ -v
```

### Configuration

Create a `.env` file in the `backend/` directory:

```bash
HA_HOST=192.168.1.50
HA_PORT=8123
HA_ACCESS_TOKEN=your_long_lived_access_token
DATABASE_URL=sqlite:///./ha_dashboard.db
```

### Running the Application

```bash
# Start the backend server
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# In another terminal, start the frontend (if React is set up)
cd frontend
npm install
npm start
```

## API Documentation

The application provides a comprehensive REST API documented with OpenAPI/Swagger:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Home Assistant Connection
- `GET /api/ha/connection` - Get HA connection status
- `POST /api/ha/connect` - Connect to Home Assistant
- `GET /api/ha/discover` - Discover all entities

#### Entity Management
- `GET /api/entities` - List all cached entities
- `GET /api/entities/{entity_id}` - Get specific entity details
- `GET /api/entities/search?q=query` - Search entities by name or ID
- `GET /api/entities/domain/{domain}` - Filter entities by domain

#### Dashboard Management
- `GET /api/dashboard/widgets` - List all dashboard widgets
- `POST /api/dashboard/widgets` - Create a new widget
- `PUT /api/dashboard/widgets/{widget_id}` - Update a widget
- `DELETE /api/dashboard/widgets/{widget_id}` - Delete a widget

## Deployment

### Docker Compose (Recommended)

```bash
# Build and start with Docker Compose
docker-compose up --build

# Or in detached mode
docker-compose up -d
```

### Bare Metal Installation

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run migrations (if any)
alembic upgrade head

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Development

### Running Tests

```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html
```

### Code Style

This project uses:
- **Black** for code formatting
- **Flake8** for linting
- **Mypy** for type checking

```bash
# Format code
black backend/app/ backend/tests/

# Lint code
flake8 backend/app/ backend/tests/ --max-line-length=120

# Type check
mypy backend/app/
```

## Project Structure

```
ha-dashboard-builder/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes and schemas
│   │   ├── services/     # Business logic (HA client, entity discovery)
│   │   └── main.py       # FastAPI application entry point
│   ├── tests/            # Comprehensive test suite
│   └── requirements.txt  # Python dependencies
├── frontend/             # React frontend (if applicable)
├── .github/workflows/    # CI/CD pipelines
├── docker-compose.yml    # Docker Compose configuration
└── README.md             # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Home Assistant](https://www.home-assistant.io/) - The open-source home automation platform
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework for building APIs
- [React](https://react.dev/) - JavaScript library for building user interfaces
