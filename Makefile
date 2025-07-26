### Defensive settings for make:
#     https://tech.davis-hansson.com/p/make/
SHELL:=bash
.ONESHELL:
.SHELLFLAGS:=-xeu -o pipefail -O inherit_errexit -c
.SILENT:
.DELETE_ON_ERROR:
MAKEFLAGS+=--warn-undefined-variables
MAKEFLAGS+=--no-builtin-rules

CURRENT_DIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
GIT_FOLDER=$(CURRENT_DIR)/.git

PROJECT_NAME=knowledge-curator
STACK_NAME=knowledge-curator-lundandco-net

VOLTO_VERSION=$(shell cat frontend/mrs.developer.json | python -c "import sys, json; print(json.load(sys.stdin)['core']['tag'])")
PLONE_VERSION=$(shell cat backend/version.txt)

# We like colors
# From: https://coderwall.com/p/izxssa/colored-makefile-for-golang-projects
RED=`tput setaf 1`
GREEN=`tput setaf 2`
RESET=`tput sgr0`
YELLOW=`tput setaf 3`

.PHONY: all
all: install

# Add the following 'help' target to your Makefile
# And add help text after each target name starting with '\#\#'
.PHONY: help
help: ## This help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

###########################################
# Frontend
###########################################
.PHONY: frontend-install
frontend-install:  ## Install React Frontend
	$(MAKE) -C "./frontend/" install

.PHONY: frontend-build
frontend-build:  ## Build React Frontend
	$(MAKE) -C "./frontend/" build

.PHONY: frontend-start
frontend-start:  ## Start React Frontend
	$(MAKE) -C "./frontend/" start

.PHONY: frontend-test
frontend-test:  ## Test frontend codebase
	@echo "Test frontend"
	$(MAKE) -C "./frontend/" test

###########################################
# Backend
###########################################
.PHONY: backend-install
backend-install:  ## Create virtualenv and install Plone
	$(MAKE) -C "./backend/" install
	$(MAKE) backend-create-site

.PHONY: backend-build
backend-build:  ## Build Backend
	$(MAKE) -C "./backend/" install

.PHONY: backend-create-site
backend-create-site: ## Create a Plone site with default content
	$(MAKE) -C "./backend/" create-site

.PHONY: backend-create-demo-data
backend-create-demo-data: ## Create demo data for React learning scenario
	$(MAKE) -C "./backend/" create-demo-data

.PHONY: backend-start-with-demo
backend-start-with-demo: ## Start Backend with fresh demo data
	$(MAKE) -C "./backend/" start-with-demo

.PHONY: backend-update-example-content
backend-update-example-content: ## Export example content inside package
	$(MAKE) -C "./backend/" update-example-content

.PHONY: backend-start
backend-start: ## Start Plone Backend
	$(MAKE) -C "./backend/" start

.PHONY: backend-test
backend-test:  ## Test backend codebase
	@echo "Test backend"
	$(MAKE) -C "./backend/" test

###########################################
# Environment
###########################################
.PHONY: install
install:  ## Install
	@echo "Install Backend & Frontend"
	$(MAKE) backend-install
	$(MAKE) frontend-install

.PHONY: clean
clean:  ## Clean installation
	@echo "Clean installation"
	$(MAKE) -C "./backend/" clean
	$(MAKE) -C "./frontend/" clean

###########################################
# QA
###########################################
.PHONY: format
format:  ## Format codebase
	@echo "Format the codebase"
	$(MAKE) -C "./backend/" format
	$(MAKE) -C "./frontend/" format

.PHONY: lint
lint:  ## Format codebase
	@echo "Lint the codebase"
	$(MAKE) -C "./backend/" lint
	$(MAKE) -C "./frontend/" lint

.PHONY: check
check:  format lint ## Lint and Format codebase

###########################################
# i18n
###########################################
.PHONY: i18n
i18n:  ## Update locales
	@echo "Update locales"
	$(MAKE) -C "./backend/" i18n
	$(MAKE) -C "./frontend/" i18n

###########################################
# Testing
###########################################
.PHONY: test
test:  backend-test frontend-test ## Test codebase

###########################################
# Container images
###########################################
.PHONY: build-images
build-images:  ## Build container images
	@echo "Build"
	$(MAKE) -C "./backend/" build-image
	$(MAKE) -C "./frontend/" build-image

###########################################
# AI Infrastructure Services
###########################################
.PHONY: ai-start
ai-start:  ## AI Services: Start AI Infrastructure (Qdrant, Redis, MailHog)
	@echo "Start AI Infrastructure services"
	DELETE_EXISTING=$(DELETE_EXISTING) VOLTO_VERSION=$(VOLTO_VERSION) PLONE_VERSION=$(PLONE_VERSION) docker compose --profile ai up -d --build
	@echo "Services available:"
	@echo "  - Qdrant (Vector DB): http://localhost:6333"
	@echo "  - Redis (Cache): localhost:6379"
	@echo "  - MailHog (Email): http://localhost:8025"

.PHONY: ai-stop
ai-stop:  ## AI Services: Stop AI Infrastructure 
	@echo "Stop AI Infrastructure services"
	@docker compose --profile ai stop

.PHONY: ai-status
ai-status:  ## AI Services: Check Status
	@echo "Check AI Infrastructure services status"
	@docker compose --profile ai ps

.PHONY: web-start
web-start:  ## Web Services: Start Web Application (Frontend, Backend, DB)
	@echo "Start Web Application services"
	DELETE_EXISTING=$(DELETE_EXISTING) VOLTO_VERSION=$(VOLTO_VERSION) PLONE_VERSION=$(PLONE_VERSION) docker compose --profile web up -d --build
	@echo "Now visit: http://knowledge-curator.localhost:8080"

.PHONY: web-stop
web-stop:  ## Web Services: Stop Web Application
	@echo "Stop Web Application services"
	@docker compose --profile web stop

.PHONY: web-status
web-status:  ## Web Services: Check Status
	@echo "Check Web Application services status"
	@docker compose --profile web ps

.PHONY: integration-start
integration-start:  ## Integration: Start AI + Web Services 
	@echo "Start Full Integration Stack"
	DELETE_EXISTING=$(DELETE_EXISTING) VOLTO_VERSION=$(VOLTO_VERSION) PLONE_VERSION=$(PLONE_VERSION) docker compose --profile integration up -d --build
	@echo "Full stack available:"
	@echo "  - Main Site: http://knowledge-curator.localhost"
	@echo "  - Classic UI: http://knowledge-curator.localhost/ClassicUI (admin/admin)"
	@echo "  - API: http://knowledge-curator.localhost/++api++"
	@echo "  - Qdrant: http://localhost:6333"
	@echo "  - MailHog: http://localhost:8025"

.PHONY: integration-stop
integration-stop:  ## Integration: Stop All Services
	@echo "Stop Full Integration Stack"
	@docker compose --profile integration stop

.PHONY: integration-status
integration-status:  ## Integration: Check Status
	@echo "Check Full Integration Stack status"
	@docker compose --profile integration ps

.PHONY: full-start
full-start:  ## Full Stack: Start Everything (Alias for integration-start)
	$(MAKE) integration-start

.PHONY: full-stop
full-stop:  ## Full Stack: Stop Everything
	@echo "Stop All Services"
	@docker compose down

.PHONY: full-clean
full-clean:  ## Full Stack: Remove All Services and Volumes
	@echo "Remove Full Docker Stack"
	@docker compose down --volumes --remove-orphans
	@echo "Remove all volume data"
	@docker volume rm $(PROJECT_NAME)_vol-site-data $(PROJECT_NAME)_vol-qdrant-data $(PROJECT_NAME)_vol-redis-data 2>/dev/null || true

.PHONY: health-check
health-check:  ## Check Health of All Running Services
	@echo "Checking service health..."
	@docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

###########################################
# Quick Development
###########################################
.PHONY: start
start:  ## Start: Knowledge Curator with demo data (alias for quick-start)
	$(MAKE) quick-start

.PHONY: quick-start
quick-start:  ## Quick Start: Full integration environment with demo data
	@echo "🚀 Starting Knowledge Curator Development Environment with Demo Data..."
	$(MAKE) integration-start
	@echo ""
	@echo "✅ Knowledge Curator is ready with React Learning Demo!"
	@echo "📚 Demo Scenario: React Development Mastery Learning Path"
	@echo "🌐 Main Site: http://knowledge-curator.localhost:8080"
	@echo "🔧 Classic UI: http://knowledge-curator.localhost:8080/ClassicUI (admin/admin)"
	@echo "📡 API: http://knowledge-curator.localhost:8080/++api++"
	@echo "🧠 Vector DB: http://localhost:6333"
	@echo "📧 Email Test: http://localhost:8025"
	@echo ""
	@echo "📝 Demo includes:"
	@echo "  - 8 Knowledge Items (JavaScript, React concepts)"
	@echo "  - 1 Learning Goal (React Development Mastery)"
	@echo "  - 1 Project Log (Portfolio Website Project)"
	@echo "  - 2 Research Notes (Best practices, Hook questions)"
	@echo "  - 3 Bookmark+ resources (Documentation, guides)"

.PHONY: quick-start-clean
quick-start-clean:  ## Quick Start: Full integration environment without demo data
	@echo "🚀 Starting Knowledge Curator Development Environment (Clean)..."
	CREATE_DEMO_DATA=0 $(MAKE) integration-start
	@echo ""
	@echo "✅ Knowledge Curator is ready (no demo data)!"
	@echo "🌐 Main Site: http://knowledge-curator.localhost:8080"
	@echo "🔧 Classic UI: http://knowledge-curator.localhost:8080/ClassicUI (admin/admin)"
	@echo "📡 API: http://knowledge-curator.localhost:8080/++api++"
	@echo "🧠 Vector DB: http://localhost:6333"
	@echo "📧 Email Test: http://localhost:8025"

.PHONY: quick-clean
quick-clean:  ## Quick Clean: Stop everything and clean up
	@echo "🧹 Cleaning up Knowledge Curator environment..."
	$(MAKE) full-clean
	@echo "✅ Environment cleaned!"

###########################################
# Local Stack
###########################################
.PHONY: stack-create-site
stack-create-site:  ## Local Stack: Create a new site
	@echo "Create a new site in the local Docker stack"
	@echo "(Stack must not be running already.)"
	DELETE_EXISTING=$(DELETE_EXISTING) VOLTO_VERSION=$(VOLTO_VERSION) PLONE_VERSION=$(PLONE_VERSION) docker compose -f docker-compose.yml run --build backend ./docker-entrypoint.sh create-site

.PHONY: stack-start
stack-start:  ## Local Stack: Start Services
	@echo "Start local Docker stack"
	DELETE_EXISTING=$(DELETE_EXISTING) VOLTO_VERSION=$(VOLTO_VERSION) PLONE_VERSION=$(PLONE_VERSION) docker compose -f docker-compose.yml up -d --build
	@echo "Now visit: http://knowledge-curator.localhost:8080"

.PHONY: stack-status
stack-status:  ## Local Stack: Check Status
	@echo "Check the status of the local Docker stack"
	@docker compose -f docker-compose.yml ps

.PHONY: stack-stop
stack-stop:  ##  Local Stack: Stop Services
	@echo "Stop local Docker stack"
	@docker compose -f docker-compose.yml stop

.PHONY: stack-rm
stack-rm:  ## Local Stack: Remove Services and Volumes
	@echo "Remove local Docker stack"
	@docker compose -f docker-compose.yml down
	@echo "Remove local volume data"
	@docker volume rm $(PROJECT_NAME)_vol-site-data

###########################################
# Acceptance
###########################################
.PHONY: acceptance-backend-dev-start
acceptance-backend-dev-start:
	@echo "Start acceptance backend"
	$(MAKE) -C "./backend/" acceptance-backend-start

.PHONY: acceptance-frontend-dev-start
acceptance-frontend-dev-start:
	@echo "Start acceptance frontend"
	$(MAKE) -C "./frontend/" acceptance-frontend-dev-start

.PHONY: acceptance-test
acceptance-test:
	@echo "Start acceptance tests in interactive mode"
	$(MAKE) -C "./frontend/" acceptance-test

# Build Docker images
.PHONY: acceptance-frontend-image-build
acceptance-frontend-image-build:
	@echo "Build acceptance frontend image"
	@docker build frontend -t GitHub/knowledge-curator-frontend:acceptance -f frontend/Dockerfile --build-arg VOLTO_VERSION=$(VOLTO_VERSION)

.PHONY: acceptance-backend-image-build
acceptance-backend-image-build:
	@echo "Build acceptance backend image"
	@docker build backend -t GitHub/knowledge-curator-backend:acceptance -f backend/Dockerfile.acceptance --build-arg PLONE_VERSION=$(PLONE_VERSION)

.PHONY: acceptance-images-build
acceptance-images-build: ## Build Acceptance frontend/backend images
	$(MAKE) acceptance-backend-image-build
	$(MAKE) acceptance-frontend-image-build

.PHONY: acceptance-frontend-container-start
acceptance-frontend-container-start:
	@echo "Start acceptance frontend"
	@docker run --rm -p 3000:3000 --name knowledge-curator-frontend-acceptance --link knowledge-curator-backend-acceptance:backend -e RAZZLE_API_PATH=http://localhost:55001/plone -e RAZZLE_INTERNAL_API_PATH=http://backend:55001/plone -d GitHub/knowledge-curator-frontend:acceptance

.PHONY: acceptance-backend-container-start
acceptance-backend-container-start:
	@echo "Start acceptance backend"
	@docker run --rm -p 55001:55001 --name knowledge-curator-backend-acceptance -d GitHub/knowledge-curator-backend:acceptance

.PHONY: acceptance-containers-start
acceptance-containers-start: ## Start Acceptance containers
	$(MAKE) acceptance-backend-container-start
	$(MAKE) acceptance-frontend-container-start

.PHONY: acceptance-containers-stop
acceptance-containers-stop: ## Stop Acceptance containers
	@echo "Stop acceptance containers"
	@docker stop knowledge-curator-frontend-acceptance
	@docker stop knowledge-curator-backend-acceptance

.PHONY: ci-acceptance-test
ci-acceptance-test:
	@echo "Run acceptance tests in CI mode"
	$(MAKE) acceptance-containers-start
	pnpm dlx wait-on --httpTimeout 20000 http-get://localhost:55001/plone http://localhost:3000
	$(MAKE) -C "./frontend/" ci-acceptance-test
	$(MAKE) acceptance-containers-stop
