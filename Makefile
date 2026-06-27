# Project configurations
PROJECT_ID ?= $(shell gcloud config get-value project 2>/dev/null)
REGION ?= asia-northeast1
TF_STATE_BUCKET ?= kintai-sync-tfstate-$(PROJECT_ID)
TF_SA_NAME ?= kintai-sync-terraform-sa
TF_SA_EMAIL ?= $(TF_SA_NAME)@$(PROJECT_ID).iam.gserviceaccount.com
APP_PREFIX ?= kintai-sync

.PHONY: help setup check generate lint opa test plan deploy destroy prune template logs secrets register-user

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Initial setup (create tfstate bucket, SA, and IAM roles)
	@echo "--- Step 1: Enabling necessary Bootstrap APIs ---"
	gcloud services enable cloudresourcemanager.googleapis.com iam.googleapis.com serviceusage.googleapis.com --project $(PROJECT_ID)
	
	@echo "--- Step 2: Checking/Creating TF State Bucket: gs://$(TF_STATE_BUCKET) ---"
	@if ! gsutil ls -b gs://$(TF_STATE_BUCKET) >/dev/null 2>&1; then \
		echo "Creating bucket gs://$(TF_STATE_BUCKET)..."; \
		gsutil mb -l $(REGION) gs://$(TF_STATE_BUCKET); \
		gsutil versioning set on gs://$(TF_STATE_BUCKET); \
	else \
		echo "Bucket already exists."; \
	fi

	@echo "--- Step 3: Checking/Creating Terraform Service Account: $(TF_SA_NAME) ---"
	@if ! gcloud iam service-accounts describe $(TF_SA_EMAIL) --project $(PROJECT_ID) >/dev/null 2>&1; then \
		echo "Creating Service Account $(TF_SA_NAME)..."; \
		gcloud iam service-accounts create $(TF_SA_NAME) \
			--project $(PROJECT_ID) \
			--display-name "Terraform Execution Account"; \
	else \
		echo "Service Account already exists."; \
	fi

	@echo "--- Step 4: Granting IAM Roles to $(TF_SA_NAME) ---"
	@for role in roles/editor roles/secretmanager.admin roles/iam.serviceAccountAdmin roles/resourcemanager.projectIamAdmin roles/storage.admin; do \
		echo "Granting $$role..."; \
		gcloud projects add-iam-policy-binding $(PROJECT_ID) \
			--member="serviceAccount:$(TF_SA_EMAIL)" \
			--role="$$role" \
			--quiet >/dev/null; \
	done

	@echo "--- Step 5: Initializing Terraform ---"
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
	uv run pytest --cov=src

plan: ## Preview infrastructure changes
	cd terraform && terraform plan -var="project_id=$(PROJECT_ID)"

deploy: ## Deploy the infrastructure
	cd terraform && terraform apply -var="project_id=$(PROJECT_ID)" -auto-approve

destroy: ## Completely destroy all infrastructure including bootstrap resources
	@echo "--- Step 1: Terraform Destroy ---"
	cd terraform && terraform destroy -var="project_id=$(PROJECT_ID)" -auto-approve
	
	@echo "--- Step 2: Removing IAM Bindings for SA ---"
	@for role in roles/editor roles/secretmanager.admin roles/iam.serviceAccountAdmin roles/resourcemanager.projectIamAdmin roles/storage.admin; do \
		echo "Removing $$role..."; \
		gcloud projects remove-iam-policy-binding $(PROJECT_ID) \
			--member="serviceAccount:$(TF_SA_EMAIL)" \
			--role="$$role" \
			--quiet >/dev/null || true; \
	done

	@echo "--- Step 3: Deleting Service Account ---"
	@gcloud iam service-accounts delete $(TF_SA_EMAIL) --project $(PROJECT_ID) --quiet || true

	@echo "--- Step 4: Deleting TF State Bucket ---"
	@gsutil rm -r gs://$(TF_STATE_BUCKET) || true
	@echo "Infrastructure and bootstrap resources destroyed."

register-user: ## Register/Update a user's Jobcan password in Secret Manager
	@read -p "Enter Jobcan Staff Code: " staff_code; \
	read -s -p "Enter Jobcan Password: " password; echo; \
	secret_id="JOBCAN_PASSWORD_$$staff_code"; \
	if ! gcloud secrets describe $$secret_id --project $(PROJECT_ID) >/dev/null 2>&1; then \
		echo "Creating secret $$secret_id..."; \
		gcloud secrets create $$secret_id --project $(PROJECT_ID) --replication-policy="automatic"; \
	fi; \
	echo -n "$$password" | gcloud secrets versions add $$secret_id --project $(PROJECT_ID) --data-file=-; \
	echo "Successfully registered password for $$staff_code."

logs: ## View recent application logs
	@echo "Fetching logs for 'kintai-sync' services..."
	gcloud logging read "resource.type=(cloud_run_revision) AND resource.labels.service_name:(kintai-sync)" --limit 50 --format="table(timestamp,textPayload)"

secrets: ## List registered secrets
	@gcloud secrets list --project $(PROJECT_ID) --filter="name:kintai-sync OR name:JOBCAN_PASSWORD"

prune: ## Interactively remove unused directories (SSoT artifacts)
	@echo "Pruning unused artifacts..."
	find . -name "*.tmp" -type d -exec rm -rf {} +

template: generate ## Alias for generate (backwards compatibility)
