# ============================================================================
# Image Storage - Local Development Makefile
#
# Purpose:
#   - Manage local development using LocalStack, SAM, and Poetry
#   - Provide developer-friendly commands for setup, testing, deployment
#   - Keep CI-friendly, reproducible workflows
#
# Philosophy:
#   - Makefile is the single entry point
#   - Intent-based commands (not raw AWS CLI usage)
#   - Safe defaults, override-friendly
# ============================================================================

.DEFAULT_GOAL := help
SHELL := /bin/bash

# ============================================================================
# Phony Targets
# ============================================================================

.PHONY: \
	help bootstrap \
	poetry-install poetry-update poetry-lock poetry-check poetry-show poetry-export poetry-activate \
	pre-commit pre-commit-clean lint format type-check test coverage clean \
	docker-up docker-down docker-restart docker-status docker-health docker-build \
	docker-logs docker-clean \
	docker-shell-localstack docker-shell-swagger \
	docker-logs-localstack docker-logs-swagger \
	openapi-validate openapi-upload \
	ls-resources ls-s3 ls-dynamodb scan-dynamodb ls-s3-objects \
	ls-lambda ls-api-id ls-api-key ls-api \
	cf-build cf-deploy cf-status cf-logs cf-delete \
	seed cleanup-seed guard-api \
	restart-hard clean-local

# ============================================================================
# Configuration
# ============================================================================

STACK_NAME := image-storage-service-snd
API_NAME   := image-storage-api-snd

AWS_REGION := us-east-1
ENDPOINT   := http://localhost:4566

TEMPLATE       := infra/template.yaml
BUILD_TEMPLATE := .aws-sam/build/template.yaml

OPENAPI_FILE   := openapi/api.yaml
OPENAPI_BUCKET := image-storage-sam-artifacts
OPENAPI_KEY    := openapi/api.yaml

# --------------------
# Docker configuration (VARIABLE-DRIVEN)
# --------------------
DOCKER_COMPOSE_FILE := docker-compose.yml

LOCALSTACK_SERVICE  := localstack
SWAGGER_SERVICE     := swagger-ui

DOCKER_SERVICES := $(LOCALSTACK_SERVICE) $(SWAGGER_SERVICE)

TEST ?=

AWS_ENV := AWS_ACCESS_KEY_ID=test \
           AWS_SECRET_ACCESS_KEY=test \
           AWS_DEFAULT_REGION=$(AWS_REGION) \
           AWS_ENDPOINT_URL=$(ENDPOINT)

# --------------------
# Seed data
# --------------------
SEED_DIR        := seed
SEED_PYTHON     := $(SEED_DIR)/seed_images.py
SEED_CLEANUP_PYTHON     := $(SEED_DIR)/cleanup_images.py
SEED_USER_ID ?= user123

# --------------------
# Default resource names (can be overridden)
# --------------------
DYNAMODB_TABLE ?= image-storage-metadata-snd
S3_BUCKET      ?= image-storage-images-snd

# --------------------
# API Gateway Auto-Discovery (LocalStack)
# --------------------
define GET_API_ID
$(shell $(AWS_ENV) aws apigateway get-rest-apis \
  --query "items[?name=='$(API_NAME)'].id | [0]" \
  --output text)
endef

define GET_API_KEY
$(shell \
  API_ID="$(call GET_API_ID)"; \
  USAGE_PLAN_ID=$$($(AWS_ENV) aws apigateway get-usage-plans \
    --query "items[?apiStages[?apiId=='$$API_ID']].id | [0]" \
    --output text); \
  API_KEY_ID=$$($(AWS_ENV) aws apigateway get-usage-plan-keys \
    --usage-plan-id $$USAGE_PLAN_ID \
    --query "items[0].id" \
    --output text); \
  $(AWS_ENV) aws apigateway get-api-key \
    --api-key $$API_KEY_ID \
    --include-value \
    --query "value" \
    --output text \
)
endef

API_ID  ?= $(call GET_API_ID)
API_KEY ?= $(call GET_API_KEY)

# ============================================================================
# Help
# ============================================================================

help:
	@echo ""
	@echo "Image Storage – Development Tasks"
	@echo ""
	@echo "Setup:"
	@echo "  make bootstrap            Bootstrap local environment"
	@echo ""
	@echo "Poetry:"
	@echo "  make poetry-install       Install dependencies"
	@echo "  make poetry-update        Update dependencies"
	@echo "  make poetry-lock          Generate poetry.lock"
	@echo "  make poetry-check         Validate pyproject.toml"
	@echo "  make poetry-show          Show dependency tree"
	@echo "  make poetry-export        Export production requirements"
	@echo "  make poetry-activate      Activate Poetry virtualenv"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint                 Run pre-commit hooks"
	@echo "  make format               Format code"
	@echo "  make type-check           Run mypy"
	@echo "  make coverage             Run tests with coverage"
	@echo "  make clean                Remove build artifacts"
	@echo ""
	@echo "Tests:"
	@echo "  make test                 Run functional tests"
	@echo "  make e2e-test             Run end-to-end tests (API Gateway + Lambda)"
	@echo ""
	@echo "Docker / LocalStack:"
	@echo "  make docker-up            Start LocalStack"
	@echo "  make docker-down          Stop containers"
	@echo "  make docker-restart       Restart LocalStack"
	@echo "  make docker-status        Show LocalStack status"
	@echo "  make docker-health        Show LocalStack health"
	@echo "  make docker-logs          Follow container logs"
	@echo "  make docker-clean         Reset Docker resources"
	@echo "  make docker-shell-localstack | docker-shell-swagger"
	@echo ""
	@echo "OpenAPI:"
	@echo "  make openapi-validate     Validate OpenAPI specification"
	@echo "  make openapi-upload       Upload OpenAPI spec to S3"
	@echo ""
	@echo "LocalStack Resources:"
	@echo "  make ls-s3                List S3 buckets"
	@echo "  make ls-dynamodb          List DynamoDB tables"
	@echo "  make scan-dynamodb        Scan DynamoDB table items"
	@echo "  make ls-s3-objects        List uploaded S3 objects"
	@echo "  make ls-lambda            List Lambda functions"
	@echo "  make ls-api-id            Show API Gateway REST API IDs"
	@echo "  make ls-api-key           Show API Gateway API key"
	@echo "  make ls-api               Show API ID + API key"
	@echo "  make ls-resources         List all LocalStack resources"
	@echo ""
	@echo "CloudFormation / SAM:"
	@echo "  make cf-build             Build SAM application"
	@echo "  make cf-deploy            Deploy stack to LocalStack"
	@echo "  make cf-status            Show stack status"
	@echo "  make cf-logs              Show stack events"
	@echo "  make cf-delete            Delete stack"
	@echo ""
	@echo "Convenience:"
	@echo "  make restart-hard         Full reset and redeploy"
	@echo ""
	@echo "Logs:"
	@echo "  make lambda-log-groups    List Lambda CloudWatch log groups"
	@echo "  make lambda-logs          Show latest Lambda logs (FUNCTION=name)"
	@echo ""
	@echo "Seed Data:"
	@echo "  make seed                 Seed images via API Gateway"
	@echo "  make cleanup-seed         Cleanup seeded images"
	@echo ""

# ============================================================================
# Bootstrap
# ============================================================================

bootstrap:
	@chmod +x scripts/bootstrap.sh
	@./scripts/bootstrap.sh

# ============================================================================
# Poetry
# ============================================================================

poetry-install:
	@poetry install

poetry-update:
	@poetry update

poetry-lock:
	@poetry lock

poetry-check:
	@poetry check

poetry-show:
	@poetry show --tree

poetry-export:
	@poetry export --only main -f requirements.txt -o src/requirements.txt

poetry-activate:
	@VENV="$$(poetry env info --path)"; \
	echo "Activating $$VENV"; \
	exec bash --rcfile <(echo "source $$VENV/bin/activate")

# ============================================================================
# Code Quality
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

coverage:
	@poetry run pytest --cov=src --cov-report=term-missing -v

clean:
	@rm -rf .aws-sam build dist .coverage htmlcov .pytest_cache
	@find . -type d -name __pycache__ -exec rm -rf {} + || true

# ============================================================================
# functional Tests
# ============================================================================
test:
	@poetry run pytest -v -s tests/functional $(TEST)

# ============================================================================
# E2E Tests (HTTP + Deployed Stack)
# ============================================================================
e2e-test: guard-api
	@echo "Running E2E tests (requires deployed stack)..."
	@poetry run pytest -v -s tests/e2e $(TEST)

# ============================================================================
# Docker / LocalStack
# ============================================================================

docker-up:
	@echo "Starting Docker services: $(DOCKER_SERVICES)"
	@docker compose -f $(DOCKER_COMPOSE_FILE) up -d $(DOCKER_SERVICES)

docker-down:
	@docker compose -f $(DOCKER_COMPOSE_FILE) down

docker-restart:
	@docker compose -f $(DOCKER_COMPOSE_FILE) restart $(DOCKER_SERVICES)

docker-status:
	@docker compose -f $(DOCKER_COMPOSE_FILE) ps

docker-health:
	@curl -sf $(ENDPOINT)/_localstack/health | python3 -m json.tool \
	  || echo "LocalStack not responding"

docker-build:
	@docker compose -f $(DOCKER_COMPOSE_FILE) build $(DOCKER_SERVICES)

docker-logs:
	@docker compose -f $(DOCKER_COMPOSE_FILE) logs -f $(DOCKER_SERVICES)

# --------------------
# Individual service access (ONE service only)
# --------------------

docker-shell-localstack:
	@docker compose -f $(DOCKER_COMPOSE_FILE) exec $(LOCALSTACK_SERVICE) sh

docker-shell-swagger:
	@docker compose -f $(DOCKER_COMPOSE_FILE) exec $(SWAGGER_SERVICE) sh

docker-logs-localstack:
	@docker compose -f $(DOCKER_COMPOSE_FILE) logs -f $(LOCALSTACK_SERVICE)

docker-logs-swagger:
	@docker compose -f $(DOCKER_COMPOSE_FILE) logs -f $(SWAGGER_SERVICE)

docker-clean:
	@echo "Cleaning Docker resources for this project only..."
	@docker compose -f $(DOCKER_COMPOSE_FILE) down \
		--volumes \
		--remove-orphans \
		--rmi local

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
	@$(AWS_ENV) aws dynamodb list-tables --output table

ls-lambda:
	@$(AWS_ENV) aws lambda list-functions \
	  --query 'Functions[*].[FunctionName,Runtime]' --output table

ls-api-id:
	@$(AWS_ENV) aws apigateway get-rest-apis \
	  --query 'items[*].[name,id]' --output table

ls-api-key:
	@API_ID=$$($(AWS_ENV) aws apigateway get-rest-apis \
	  --query "items[?name=='$(API_NAME)'].id | [0]" --output text); \
	USAGE_PLAN_ID=$$($(AWS_ENV) aws apigateway get-usage-plans \
	  --query "items[?apiStages[?apiId=='$$API_ID']].id | [0]" --output text); \
	API_KEY_ID=$$($(AWS_ENV) aws apigateway get-usage-plan-keys \
	  --usage-plan-id $$USAGE_PLAN_ID --query "items[0].id" --output text); \
	API_KEY_VALUE=$$($(AWS_ENV) aws apigateway get-api-key \
	  --api-key $$API_KEY_ID --include-value --query 'value' --output text); \
	BLUE='\033[34m'; RESET='\033[0m'; \
	echo "+-------------------------------------------------------------------+"; \
	echo "|                       GetApiKey                                    |"; \
	echo "+------------------------+------------------------------------------+"; \
	printf "|  %b%-20s%b |  %b%-38s%b |\n" \
	  "$$BLUE" "$(API_NAME)" "$$RESET" \
	  "$$BLUE" "$$API_KEY_VALUE" "$$RESET"; \
	echo "+------------------------+------------------------------------------+"

ls-api: ls-api-id ls-api-key

ls-resources: ls-s3 ls-dynamodb ls-lambda ls-api-id

scan-dynamodb:
	@echo "Scanning DynamoDB table: $(DYNAMODB_TABLE)"
	@$(AWS_ENV) aws dynamodb scan \
	  --table-name $(DYNAMODB_TABLE)

ls-s3-objects:
	@echo "Listing S3 objects in bucket: $(S3_BUCKET)"
	@$(AWS_ENV) aws s3 ls s3://$(S3_BUCKET) --recursive


# ============================================================================
# Lambda Logs
# ============================================================================

lambda-logs:
	@if [ -z "$(FUNCTION)" ]; then \
	  echo "Usage: make lambda-logs FUNCTION=<lambda-name>"; exit 1; \
	fi; \
	LOG_GROUP="/aws/lambda/$(FUNCTION)"; \
	LOG_STREAM=$$($(AWS_ENV) aws logs describe-log-streams \
	  --log-group-name "$$LOG_GROUP" \
	  --order-by LastEventTime \
	  --descending \
	  --query 'logStreams[0].logStreamName' \
	  --output text); \
	if [ "$$LOG_STREAM" = "None" ] || [ -z "$$LOG_STREAM" ]; then \
	  echo "No log streams yet for $(FUNCTION)."; \
	  echo "Invoke the Lambda once (API call or aws lambda invoke) and retry."; \
	  exit 0; \
	fi; \
	$(AWS_ENV) aws logs get-log-events \
	  --log-group-name "$$LOG_GROUP" \
	  --log-stream-name "$$LOG_STREAM" \
	  --limit 50 \
	  --query 'events[*].message' \
	  --output text

lambda-log-groups:
	@$(AWS_ENV) aws logs describe-log-groups \
	  --log-group-name-prefix "/aws/lambda" \
	  --query 'logGroups[*].logGroupName' \
	  --output table

# ============================================================================
# CloudFormation / SAM
# ============================================================================

cf-build: poetry-export
	@poetry run sam build --template-file $(TEMPLATE)

cf-deploy: docker-up openapi-validate openapi-upload cf-build
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
	  --stack-name $(STACK_NAME) --output table

cf-delete:
	@echo "Deleting CloudFormation stack: $(STACK_NAME)"
	@echo "1) Stopping Docker services..."
	@$(MAKE) docker-clean || true

	@echo "2) Cleaning LocalStack persistent data..."
	@$(MAKE) clean-local || true

# ============================================================================
# Seed & Cleanup (API-based)
#
# Validates full flow:
# API Gateway → Lambda → S3 → DynamoDB
# ============================================================================

guard-api:
	@if [ -z "$(API_ID)" ] || [ "$(API_ID)" = "None" ]; then \
	  echo "API_ID not found. Is the stack deployed?"; exit 1; \
	fi

seed: guard-api
	@poetry run python $(SEED_PYTHON) \
	  --api-id $(API_ID) \
	  --api-key $(API_KEY)

cleanup-seed: guard-api
	@poetry run python $(SEED_CLEANUP_PYTHON) \
	  --api-id $(API_ID) \
	  --api-key $(API_KEY) \
	  --user-id $(SEED_USER_ID)


# ============================================================================
# Convenience
# ============================================================================
clean-local:
	@echo "Cleaning LocalStack data and AWS SAM artifacts..."
	@rm -rf .aws-sam
	@docker run --rm \
	  -v "$$(pwd)/localstack-data:/var/lib/localstack" \
	  alpine \
	  sh -c "rm -rf /var/lib/localstack/*"

restart-hard:
	@echo "HARD RESET: wiping LocalStack and redeploying"
	@echo ""

	@echo "1) Stopping Docker services..."
	@$(MAKE) docker-clean || true

	@echo "2) Cleaning LocalStack persistent data..."
	@$(MAKE) clean-local || true

	@echo "3) Starting LocalStack..."
	@$(MAKE) docker-up

	@echo "4) Waiting for LocalStack to be healthy..."
	@sleep 10

	@echo "5) Deploying stack..."
	@$(MAKE) cf-deploy
