# Development
up:
	docker compose up

up-build:
	docker compose up --build

down:
	docker compose down

# Production
prod-up:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-down:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Logs
logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-worker:
	docker compose logs -f worker

# Cleanup
prune:
	docker system prune -f

prune-all:
	docker system prune -af --volumes

# Stats
stats:
	docker stats

# Tests
test:
	cd api && python -m pytest tests/ -v
