# Deployment Guide for HA Dashboard Builder

This guide covers different deployment options for the HA Dashboard Builder application.

## Option 1: Docker Compose (Recommended)

### Prerequisites

- Docker installed
- Docker Compose installed
- Home Assistant instance accessible on your network

### Steps

1. **Clone and configure**
   ```bash
   git clone https://github.com/yourusername/ha-dashboard-builder.git
   cd ha-dashboard-builder
   cp backend/.env.example backend/.env
   # Edit .env with your HA credentials
   ```

2. **Build and start**
   ```bash
   docker-compose up --build -d
   ```

3. **Verify deployment**
   ```bash
   # Check logs
   docker-compose logs -f
   
   # Access the application
   curl http://localhost:8000/docs
   ```

### Docker Compose Configuration

The `docker-compose.yml` file includes:
- Backend service with FastAPI
- SQLite database volume for persistence
- Health checks and restart policies

## Option 2: Bare Metal Installation

### Prerequisites

- Python 3.11+ installed
- pip package manager
- Home Assistant instance accessible on your network

### Steps

1. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your HA credentials
   ```

3. **Run the application**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Production Considerations

For production deployment, consider:
- Using `gunicorn` instead of `uvicorn` for better performance
- Setting up a reverse proxy (nginx/apache)
- Configuring proper SSL/TLS certificates
- Setting up log rotation and monitoring

## Option 3: Kubernetes Deployment

### Prerequisites

- Kubernetes cluster access
- kubectl configured
- Persistent storage available

### Steps

1. **Create namespace**
   ```bash
   kubectl create namespace ha-dashboard
   ```

2. **Deploy application**
   ```bash
   kubectl apply -f k8s/deployment.yaml
   kubectl apply -f k8s/service.yaml
   ```

3. **Configure ingress** (optional)
   ```bash
   kubectl apply -f k8s/ingress.yaml
   ```

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HA_HOST` | Home Assistant host IP | Required |
| `HA_PORT` | Home Assistant port | 8123 |
| `HA_ACCESS_TOKEN` | HA API access token | Required |
| `DATABASE_URL` | SQLite database URL | sqlite:///./ha_dashboard.db |
| `DEBUG` | Enable debug mode | false |

### Database Configuration

The application uses SQLite by default for simplicity. For production, you can switch to PostgreSQL:

```bash
DATABASE_URL=postgresql://user:password@localhost/dbname
```

## Monitoring and Health Checks

### Health Endpoint

```bash
curl http://localhost:8000/health
```

### Metrics

The application provides basic metrics at `/metrics` endpoint for integration with monitoring systems.

## Troubleshooting

### Common Issues

1. **Connection refused to HA**
   - Verify HA is running and accessible
   - Check firewall settings
   - Ensure access token is valid

2. **Database errors**
   - Check SQLite file permissions
   - Verify disk space availability

3. **Performance issues**
   - Increase cache refresh interval
   - Consider using PostgreSQL for large deployments

## Support

For deployment issues, please:
1. Check the logs (`docker-compose logs` or `journalctl`)
2. Review the configuration files
3. Open an issue with your setup details
