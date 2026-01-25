# ============================================================================
# Image Stream - Local Development Makefile
#
# Purpose:
#   - Manage local development using LocalStack, SAM, and Poetry
#   - Provide developer-friendly commands for setup, testing, deployment
#   - Keep CI-friendly and interview-ready workflows
# ============================================================================

.DEFAULT_GOAL := help
SHELL := /bin/bash

.PHONY: help bootstrap setup install \
        docker-up docker-down docker-restart docker-logs docker-ps docker-status docker-health \
        docker-build docker-pull docker-clean docker-shell \
        poetry-install poetry-update poetry-lock poetry-shell poetry-check poetry-show poetry-export poetry-export-dev \
        pre-commit pre-commit-clean lint format type-check test coverage clean \
        openapi-validate openapi-upload \
        ls-resources ls-s3 ls-dynamodb ls-lambda ls-apigateway \
        cf-build cf-deploy cf-destroy cf-status cf-logs cf-hard-destroy restart

# ============================================================================
# Configuration
# ============================================================================

STACK_NAME := image-storage-service

TEMPLATE := infra/template.yaml
BUILD_TEMPLATE := .aws-sam/build/template.yaml
API_NAME := image-storage-api-snd

AWS_REGION := us-east-1
ENDPOINT := http://localhost:4566

TEST ?=
SERVICE ?= localstack
DOCKER_COMPOSE_FILE := docker-compose.yml

OPENAPI_FILE := openapi/api.yaml
OPENAPI_BUCKET := image-storage-sam-artifacts
OPENAPI_KEY := openapi/api.yaml

# AWS credentials for LocalStack
AWS_ENV := AWS_ACCESS_KEY_ID=test \
           AWS_SECRET_ACCESS_KEY=test \
           AWS_DEFAULT_REGION=$(AWS_REGION) \
           AWS_ENDPOINT_URL=$(ENDPOINT)

# ============================================================================
# Help
# ============================================================================

help:
	@echo ""
	@echo "Image Stream - Development Tasks"
	@echo ""
	@echo "Setup:"
	@echo "  make bootstrap            Run bootstrap script"
	@echo ""
	@echo "Poetry:"
	@echo "  make poetry-install       Install dependencies"
	@echo "  make poetry-update        Update dependencies"
	@echo "  make poetry-lock          Generate poetry.lock"
	@echo "  make poetry-check         Validate pyproject.toml"
	@echo "  make poetry-show          Show dependency tree"
	@echo "  make poetry-shell         Activate virtual environment"
	@echo "  make poetry-export        Export production requirements"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint                 Run pre-commit hooks"
	@echo "  make format               Auto-format code"
	@echo "  make type-check           Run mypy"
	@echo "  make test                 Run tests"
	@echo "  make coverage             Run tests with coverage"
	@echo "  make clean                Remove build artifacts"
	@echo ""
	@echo "Docker / LocalStack:"
	@echo "  make docker-up            Start LocalStack"
	@echo "  make docker-down          Stop containers"
	@echo "  make docker-restart       Restart LocalStack"
	@echo "  make docker-status        Show LocalStack status"
	@echo "  make docker-health        Show LocalStack health"
	@echo "  make docker-logs          Follow container logs"
	@echo "  make docker-shell         Shell into container"
	@echo "  make docker-clean         Prune Docker resources"
	@echo ""
	@echo "OpenAPI:"
	@echo "  make openapi-validate     Validate OpenAPI specification"
	@echo "  make openapi-upload       Upload OpenAPI spec to S3"
	@echo ""
	@echo "CloudFormation / SAM:"
	@echo "  make cf-build             Build SAM application"
	@echo "  make cf-deploy            Deploy stack to LocalStack"
	@echo "  make cf-status            Show stack status"
	@echo "  make cf-logs              Show stack events"
	@echo "  make cf-delete           Delete stack"
	@echo ""
	@echo "LocalStack Resources:"
	@echo "  make ls-resources         List all AWS resources"
	@echo ""
	@echo "Convenience:"
	@echo "  make restart              Restart and redeploy"
	@echo ""

# ============================================================================
# Bootstrap & Setup
# ============================================================================

bootstrap:
	@chmod +x scripts/bootstrap.sh
	@./scripts/bootstrap.sh

# ============================================================================
# Poetry - Dependency Management
# ============================================================================

poetry-install:
	@poetry install

poetry-update:
	@poetry update

poetry-lock:
	@poetry lock

poetry-shell:
	@poetry shell

poetry-check:
	@poetry check

poetry-show:
	@poetry show --tree

poetry-export:
	@poetry install --only main --no-interaction
	@poetry run pip freeze \
		| grep -E '^(boto3==|pydantic==|aws-lambda-powertools==)' \
		> src/requirements.txt

# ============================================================================
# Code Quality & Testing
# ============================================================================

pre-commit:
	@poetry run pre-commit install

pre-commit-clean:
	@poetry run pre-commit clean

lint:
	@poetry run pre-commit run --all-files

format:
	@poetry run ruff format src/

type-check:
	@poetry run mypy src/

test:
	@echo "Running tests $(if $(TEST),for '$(TEST)',for entire suite)..."
	@poetry run pytest -v -s $(TEST)

coverage:
	@poetry run pytest $(TEST) --cov=src --cov-report=term-missing -v -s

clean:
	@rm -rf .aws-sam build dist *.egg-info .coverage htmlcov .pytest_cache
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# ============================================================================
# Docker / LocalStack
# ============================================================================

docker-up:
	@echo "Starting LocalStack..."
	docker compose -f $(DOCKER_COMPOSE_FILE) up -d $(SERVICE)

docker-down:
	docker compose -f $(DOCKER_COMPOSE_FILE) down

docker-restart:
	docker compose -f $(DOCKER_COMPOSE_FILE) restart $(SERVICE)

docker-ps:
	docker compose -f $(DOCKER_COMPOSE_FILE) ps

docker-status:
	@poetry run localstack status

docker-health:
	@curl -s $(ENDPOINT)/_localstack/health | python3 -m json.tool || echo "LocalStack not responding"

docker-logs:
	docker compose -f $(DOCKER_COMPOSE_FILE) logs -f $(SERVICE)

docker-build:
	docker compose -f $(DOCKER_COMPOSE_FILE) build $(SERVICE)

docker-pull:
	docker compose -f $(DOCKER_COMPOSE_FILE) pull $(SERVICE)

docker-shell:
	docker compose -f $(DOCKER_COMPOSE_FILE) exec $(SERVICE) sh

docker-clean:
	docker compose -f $(DOCKER_COMPOSE_FILE) down -v --remove-orphans
	docker volume prune -f
	docker container prune -f
	docker image prune -f

# ============================================================================
# Swagger UI
# ============================================================================
swagger-up:
	@docker compose up -d swagger-ui
	@echo "Swagger UI available at http://localhost:8080"

swagger-down:
	@docker compose stop swagger-ui

swagger-restart:
	@docker compose restart swagger-ui

swagger-logs:
	@docker compose logs -f swagger-ui

# ============================================================================
# OpenAPI
# ============================================================================

openapi-validate:
	@poetry run python3 -c "import yaml; yaml.safe_load(open('$(OPENAPI_FILE)'))"

openapi-upload:
	@$(AWS_ENV) aws s3 mb s3://$(OPENAPI_BUCKET) 2>/dev/null || true
	@$(AWS_ENV) aws s3 cp $(OPENAPI_FILE) s3://$(OPENAPI_BUCKET)/$(OPENAPI_KEY)

# ============================================================================
# LocalStack Resource Inspection
# ============================================================================

ls-s3:
	@$(AWS_ENV) aws s3 ls

ls-dynamodb:
	@$(AWS_ENV) aws dynamodb list-tables --query 'TableNames[]' --output table

ls-lambda:
	@$(AWS_ENV) aws lambda list-functions \
	  --query 'Functions[*].[FunctionName,Runtime]' --output table

ls-apigateway:
	@$(AWS_ENV) aws apigateway get-rest-apis \
	  --query 'items[*].[name,id]' --output table

ls-resources: ls-s3 ls-dynamodb ls-lambda ls-apigateway

ls-api-key:
	@echo "Fetching API Key value..."
	@echo ""
	@API_ID=$$($(AWS_ENV) aws apigateway get-rest-apis \
	  --query "items[?name=='$(API_NAME)'].id | [0]" \
	  --output text); \
	if [ "$$API_ID" = "None" ] || [ -z "$$API_ID" ]; then \
	  echo "API not found: $(API_NAME)"; exit 1; \
	fi; \
	USAGE_PLAN_ID=$$($(AWS_ENV) aws apigateway get-usage-plans \
	  --query "items[?apiStages[?apiId=='$$API_ID']].id | [0]" \
	  --output text); \
	if [ "$$USAGE_PLAN_ID" = "None" ] || [ -z "$$USAGE_PLAN_ID" ]; then \
	  echo "Usage plan not found"; exit 1; \
	fi; \
	API_KEY_ID=$$($(AWS_ENV) aws apigateway get-usage-plan-keys \
	  --usage-plan-id $$USAGE_PLAN_ID \
	  --query "items[0].id" \
	  --output text); \
	if [ "$$API_KEY_ID" = "None" ] || [ -z "$$API_KEY_ID" ]; then \
	  echo "API key not found"; exit 1; \
	fi; \
	$(AWS_ENV) aws apigateway get-api-key \
	  --api-key $$API_KEY_ID \
	  --include-value \
	  --query 'value' \
	  --output text

# ============================================================================
# CloudFormation / SAM
# ============================================================================

cf-build: poetry-export
	@poetry run sam build --template-file $(TEMPLATE)

cf-deploy: docker-up swagger-up openapi-validate openapi-upload cf-build
	@$(AWS_ENV) poetry run sam deploy \
	  --template-file $(BUILD_TEMPLATE) \
	  --stack-name $(STACK_NAME) \
	  --resolve-s3 \
	  --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
	  --region $(AWS_REGION) \
	  --no-confirm-changeset \
	  --no-fail-on-empty-changeset

cf-status:
	@$(AWS_ENV) aws cloudformation describe-stacks --stack-name $(STACK_NAME)

cf-logs:
	@$(AWS_ENV) aws cloudformation describe-stack-events \
	  --stack-name $(STACK_NAME) \
	  --query 'StackEvents[0:10].[Timestamp,LogicalResourceId,ResourceStatus]' \
	  --output table

cf-delete:
	@read -p "This will HARD DELETE the stack. Continue? [y/N] " yn; \
	[ "$$yn" = "y" ] || exit 1
	@$(AWS_ENV) aws cloudformation delete-stack --stack-name $(STACK_NAME) || true
	@$(MAKE) docker-down || true
	@$(MAKE) docker-clean || true

# ============================================================================
# Convenience
# ============================================================================

restart: docker-restart cf-deploy
