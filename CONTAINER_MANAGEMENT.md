# Knowledge Curator - Enhanced Container Management

## 🚀 Quick Start

Get started with the full Knowledge Curator development environment:

```bash
cd knowledge-curator/
make quick-start
```

**Access Points:**
- **Main Site**: http://knowledge-curator.localhost
- **Classic UI**: http://knowledge-curator.localhost/ClassicUI (admin/admin)
- **API**: http://knowledge-curator.localhost/++api++
- **Vector DB**: http://localhost:6333
- **Email Testing**: http://localhost:8025

## 📋 Architecture Overview

The Knowledge Curator uses a **profile-based Docker Compose architecture** with 3 main service groups:

### 🧠 **AI Infrastructure Services** (`--profile ai`)
- **Qdrant**: Vector database for semantic search
- **Redis**: Caching and background task queue
- **MailHog**: Email testing during development

### 🌐 **Web Application Services** (`--profile web`)
- **Traefik**: Reverse proxy and load balancer
- **Frontend**: React/Volto application
- **Backend**: Plone CMS with Knowledge Curator add-on
- **Varnish**: Caching layer
- **PostgreSQL**: Primary database
- **Purger**: Cache management

### 🔧 **Combined Profiles**
- **`integration`**: AI + Web services for full testing
- **`full`**: Alias for integration profile

## 🛠️ Container Management Commands

### AI Services Only
```bash
make ai-start      # Start AI infrastructure (Qdrant, Redis, MailHog)
make ai-stop       # Stop AI services
make ai-status     # Check AI services status
```

### Web Application Only  
```bash
make web-start     # Start web services (Frontend, Backend, DB)
make web-stop      # Stop web services
make web-status    # Check web services status
```

### Full Integration
```bash
make integration-start    # Start AI + Web services
make integration-stop     # Stop all services
make integration-status   # Check all services status
```

### Quick Commands
```bash
make quick-start   # One-command full environment startup
make quick-clean   # Stop everything and clean up volumes
make health-check  # Check health of all running services
```

## 🔧 Service Profiles Explained

### Individual Profile Usage
```bash
# AI services only
docker compose --profile ai up -d

# Web application only  
docker compose --profile web up -d

# Everything together
docker compose --profile integration up -d
```

### Service Dependencies
```
AI Services (ai):
├── qdrant (Vector Database)
├── redis (Cache/Queue)
└── mailhog (Email Testing)

Web Services (web):
├── traefik (Reverse Proxy)
├── frontend (React/Volto)
├── backend (Plone + Knowledge Curator)
├── varnish (Caching)
├── db (PostgreSQL)
└── purger (Cache Management)

Integration (integration):
└── All above services
```

## 🌐 Network Architecture

```
knowledge-net (AI Services)
├── qdrant:6333
├── redis:6379
└── mailhog:1025,8025

plone-internal (Web Services)
├── traefik:80
├── frontend:3000
├── backend:8080
├── varnish:80
└── db:5432

Backend bridges both networks for AI integration
```

## 📁 Container Data Persistence

```
Volumes:
├── vol-site-data (PostgreSQL data)
├── vol-qdrant-data (Vector database)
└── vol-redis-data (Redis persistence)
```

## 🔍 Service URLs and Access

### Web Application
- **Main Site**: http://knowledge-curator.localhost
- **Admin Interface**: http://knowledge-curator.localhost/ClassicUI
  - Username: `admin`
  - Password: `admin`
- **REST API**: http://knowledge-curator.localhost/++api++

### AI Services
- **Qdrant Dashboard**: http://localhost:6333/dashboard
- **Qdrant API**: http://localhost:6333
- **Redis**: `localhost:6379` (no web interface)
- **MailHog**: http://localhost:8025

### Development Tools
- **Traefik Dashboard**: http://traefik.knowledge-curator.localhost

## ⚡ Development Workflows

### 1. **AI Feature Development**
```bash
# Start AI services only
make ai-start

# Develop your AI features using:
# - Qdrant: http://localhost:6333  
# - Redis: localhost:6379
# - MailHog: http://localhost:8025

# Clean up
make ai-stop
```

### 2. **Frontend Development**
```bash
# Start web application
make web-start

# Access your site: http://knowledge-curator.localhost
# Make frontend changes, test functionality

# Clean up
make web-stop
```

### 3. **Full Integration Testing**
```bash
# Start everything
make quick-start

# Test complete AI + Web integration
# Verify all components work together

# Clean up completely
make quick-clean
```

## 🔧 Configuration

### Environment Variables
Available in `env.development`:
- **Database**: `DB_NAME`, `DB_HOST`, `DB_PASSWORD`
- **AI Services**: `QDRANT_HOST`, `REDIS_URL`
- **Development**: `DEBUG`, `CREATE_EXAMPLE_CONTENT`

### Custom Configuration
```bash
# Load custom environment
export $(cat env.development | xargs)
make integration-start
```

## 🚨 Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check what's running
make health-check

# Clean everything and restart
make quick-clean
make quick-start
```

**Port conflicts:**
```bash
# Check what's using ports
docker compose ps
netstat -tulpn | grep ":80\|:6333\|:6379"
```

**Database issues:**
```bash
# Reset database completely
make full-clean
make quick-start
```

**Network connectivity:**
```bash
# Check networks
docker network ls | grep knowledge

# Restart with clean networks
docker compose down
docker compose --profile integration up -d
```

## 📊 Resource Usage

### Minimum Requirements
- **RAM**: 4GB available
- **Disk**: 2GB for containers + volumes
- **CPU**: 2 cores recommended

### Service Resource Usage
- **PostgreSQL**: ~200MB RAM
- **Qdrant**: ~100MB RAM  
- **Redis**: ~50MB RAM
- **Plone Backend**: ~500MB RAM
- **Volto Frontend**: ~200MB RAM

## 🔄 Migration from Old Setup

If you were using the root-level containers:

```bash
# Stop old containers
cd /path/to/root
docker compose down

# Start new setup
cd knowledge-curator/
make quick-start
```

The new setup provides the same functionality with better organization and flexibility.

## 💡 Pro Tips

### Development Efficiency
```bash
# Quick status check
make health-check

# Logs for specific service
docker compose logs -f backend

# Shell into backend container
docker compose exec backend bash

# Reset just the database
docker compose stop db
docker volume rm knowledge-curator_vol-site-data
make integration-start
```

### AI Development
```bash
# Test Qdrant connection
curl http://localhost:6333/health

# Check Redis 
docker compose exec redis redis-cli ping

# View emails in development
open http://localhost:8025
```

This enhanced setup maintains all the professional architecture of the original Knowledge Curator while adding flexible AI service management and improved development workflows. 