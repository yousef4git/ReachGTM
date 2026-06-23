# ReachGTM dev shortcuts. Usage: `make up`, `make cold`, `make logs`, ...
COMPOSE := docker compose -f infra/docker-compose.yml

.PHONY: up build down logs ps cold psql

up:        ## Start the stack (no rebuild)
	$(COMPOSE) up -d

build:     ## Rebuild images and start
	$(COMPOSE) up --build -d

down:      ## Stop the stack (KEEPS the database)
	$(COMPOSE) down

logs:      ## Tail backend + agents logs
	$(COMPOSE) logs -f backend agents

ps:        ## Show container status
	$(COMPOSE) ps

cold:      ## WIPE the database + rebuild + start fresh (cold run)
	$(COMPOSE) down -v
	$(COMPOSE) up --build -d

psql:      ## Open a psql shell on the dev database
	docker exec -it infra-db-1 psql -U postgres -d reachgtm
