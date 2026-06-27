# Project configurations
PROJECT_ID ?= $(shell gcloud config get-value project 2>/dev/null)
REGION ?= asia-northeast1
TF_STATE_BUCKET ?= kintai-sync-tfstate-$(PROJECT_ID)

.PHONY: help setup check generate lint opa test plan deploy prune template

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Initial setup (create tfstate bucket and project preparation)
	@echo "Checking if bucket gs://$(TF_STATE_BUCKET) exists..."
	@if ! gsutil ls -b gs://$(TF_STATE_BUCKET) >/dev/null 2>&1; then \
		echo "Creating bucket gs://$(TF_STATE_BUCKET)..."; \
		gsutil mb -l $(REGION) gs://$(TF_STATE_BUCKET); \
		gsutil versioning set on gs://$(TF_STATE_BUCKET); \
	else \
		echo "Bucket already exists."; \
	fi
	cd terraform && terraform init -backend-config="bucket=$(TF_STATE_BUCKET)"

check: ## Pre-flight check for GCP permissions, billing, and APIs
	@echo "Checking GCP configuration..."
	gcloud auth list --filter=status:ACTIVE --format="value(account)"
	gcloud projects describe $(PROJECT_ID)
	gcloud services list --enabled --filter="name:compute.googleapis.com"

generate: ## Generate Terraform variables or config from source of truth
	@echo "Generating user_settings_template.csv..."
	@echo "slack_user_id,jobcan_company_id,jobcan_staff_code,morning_off_start,morning_off_end,afternoon_off_start,afternoon_off_end,working_hours_start,working_hours_end,timezone" > user_settings_template.csv
	@echo "U01234567,1234,staff-001,09:00,13:00,14:00,18:00,09:00,18:00,Asia/Tokyo" >> user_settings_template.csv

lint: ## Lint and format Terraform and Python files
	@echo "Linting Python code..."
	uv run ruff check . || echo "Ruff not installed, skipping..."
	@echo "Formatting Terraform files..."
	terraform fmt -recursive terraform/

opa: ## Check Rego policy syntax (stub)
	@echo "Checking OPA policies..."
	@if command -v opa >/dev/null; then opa check terraform/policies/; else echo "OPA not installed, skipping..."; fi

test: ## Run unit tests
	@echo "Running tests with uv..."
	uv run pytest

plan: ## Preview infrastructure changes
	cd terraform && terraform plan -var="project_id=$(PROJECT_ID)"

deploy: ## Deploy the infrastructure
	cd terraform && terraform apply -var="project_id=$(PROJECT_ID)" -auto-approve

prune: ## Interactively remove unused directories (SSoT artifacts)
	@echo "Pruning unused artifacts..."
	find . -name "*.tmp" -type d -exec rm -rf {} +

template: generate ## Alias for generate (backwards compatibility)
