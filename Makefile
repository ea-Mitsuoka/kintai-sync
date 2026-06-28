# Project configurations
PROJECT_ID ?= $(shell gcloud config get-value project 2>/dev/null)
REGION ?= asia-northeast1
TF_STATE_BUCKET ?= kintai-sync-tfstate-$(PROJECT_ID)
TEST_DATA_BUCKET ?= kintai-sync-test-data-$(PROJECT_ID)
TF_SA_NAME ?= kintai-sync-terraform-sa
TF_SA_EMAIL ?= $(TF_SA_NAME)@$(PROJECT_ID).iam.gserviceaccount.com
APP_PREFIX ?= kintai-sync
REPO_NAME ?= $(APP_PREFIX)-repo

.PHONY: help setup check generate lint opa test prepare-test plan build push deploy destroy destroy-all prune template logs secrets register-user register-secrets register-sheets-oauth

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
		sleep 5; \
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

prepare-test: ## Create a GCS bucket and upload test data for prompt optimization
	@echo "--- Checking/Creating Test Data Bucket: gs://$(TEST_DATA_BUCKET) ---"
	@if ! gsutil ls -b gs://$(TEST_DATA_BUCKET) >/dev/null 2>&1; then \
		echo "Creating bucket gs://$(TEST_DATA_BUCKET)..."; \
		gsutil mb -l $(REGION) gs://$(TEST_DATA_BUCKET); \
	else \
		echo "Bucket already exists."; \
	fi
	@echo "--- Generating test_data.csv ---"
	@echo "prompt,target_response" > test_data.csv
	@echo "「明日、有給休暇をいただきます。」,\"{\\\"target_date\\\": \\\"2026-06-29\\\", \\\"attendance_type\\\": \\\"full_day\\\", \\\"reason\\\": \\\"有給休暇\\\"}\"" >> test_data.csv
	@echo "「明日の午前中、通院のためお休みします。午後から出社します。」,\"{\\\"target_date\\\": \\\"2026-06-29\\\", \\\"attendance_type\\\": \\\"morning_off\\\", \\\"reason\\\": \\\"通院\\\"}\"" >> test_data.csv
	@echo "「本日、急用により15時で早退させていただきます。」,\"{\\\"target_date\\\": \\\"2026-06-28\\\", \\\"attendance_type\\\": \\\"early\\\", \\\"reason\\\": \\\"急用\\\"}\"" >> test_data.csv
	@echo "「来週の月曜日は午後休にします。」,\"{\\\"target_date\\\": \\\"2026-07-06\\\", \\\"attendance_type\\\": \\\"afternoon_off\\\", \\\"reason\\\": null}\"" >> test_data.csv
	@echo "「体調不良のため、本日はお休みさせてください。」,\"{\\\"target_date\\\": \\\"2026-06-28\\\", \\\"attendance_type\\\": \\\"full_day\\\", \\\"reason\\\": \\\"体調不良\\\"}\"" >> test_data.csv
	@echo "「家族が風邪を引いていますが、私は元気なので休みません。」,\"{\\\"target_date\\\": null, \\\"attendance_type\\\": \\\"none\\\", \\\"reason\\\": null}\"" >> test_data.csv
	@echo "「電車遅延のため、10時半ごろに出社します。」,\"{\\\"target_date\\\": \\\"2026-06-28\\\", \\\"attendance_type\\\": \\\"late\\\", \\\"reason\\\": \\\"電車遅延\\\"}\"" >> test_data.csv
	@echo "「明日はワーケーションのためフレックスで20時まで働きます。」,\"{\\\"target_date\\\": \\\"2026-06-29\\\", \\\"attendance_type\\\": \\\"flex\\\", \\\"reason\\\": \\\"ワーケーション\\\"}\"" >> test_data.csv
	@echo "--- Uploading test_data.csv to gs://$(TEST_DATA_BUCKET) ---"
	gsutil cp test_data.csv gs://$(TEST_DATA_BUCKET)/test_data.csv
	@echo "Upload complete: gs://$(TEST_DATA_BUCKET)/test_data.csv"

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
	uv run ruff check . || echo "Ruff check failed or not installed"
	@echo "Formatting Terraform files..."
	cd terraform && terraform fmt

test: ## Run unit tests with coverage
	uv run pytest --cov=src tests/

build: ## Build docker images locally (Placeholder logic)
	@echo "Building services..."

push: ## Push images to Artifact Registry (Placeholder logic)
	@echo "Pushing images to $(REGION)-docker.pkg.dev/..."

deploy: ## Deploy resources via Terraform
	cd terraform && terraform apply -auto-approve

destroy: ## Destroy resources managed by Terraform
	cd terraform && terraform destroy -auto-approve

destroy-all: ## Completely clean up everything including the storage bucket
	cd terraform && terraform destroy -auto-approve
	gsutil rm -r gs://$(TF_STATE_BUCKET)
	gsutil rm -r gs://$(TEST_DATA_BUCKET) || true

prune: ## Clean temporary python and testing artifacts
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".coverage" -exec rm -r {} +

template: generate ## Alias for generate

logs: ## Stream live logs from Cloud Run Worker
	gcloud beta run services logs tail $(APP_PREFIX)-worker --project $(PROJECT_ID) --region=$(REGION)

secrets: ## Check Secret Manager secrets status
	gcloud secrets list --project $(PROJECT_ID)

register-user: ## Securely register a user password in Secret Manager
	@read -p "Enter Staff Code: " staff_code; \
	read -s -p "Enter Jobcan Password: " password; \
	echo ""; \
	SECRET_ID="JOBCAN_PASSWORD_$$(echo $$staff_code | tr '-' '_')"; \
	gcloud secrets create $$SECRET_ID --replication-policy="automatic" --project $(PROJECT_ID) || true; \
	echo -n "$$password" | gcloud secrets versions add $$SECRET_ID --data-file=- --project $(PROJECT_ID)

register-secrets: ## Interactively register system global tokens
	@read -s -p "Enter Slack Bot Token (xoxb-...): " bot_token; echo ""; \
	read -s -p "Enter Slack Signing Secret: " signing_secret; echo ""; \
	gcloud secrets create $(APP_PREFIX)-slack-bot-token --replication-policy="automatic" --project $(PROJECT_ID) || true; \
	echo -n "$$bot_token" | gcloud secrets versions add $(APP_PREFIX)-slack-bot-token --data-file=- --project $(PROJECT_ID); \
	gcloud secrets create $(APP_PREFIX)-slack-signing-secret --replication-policy="automatic" --project $(PROJECT_ID) || true; \
	echo -n "$$signing_secret" | gcloud secrets versions add $(APP_PREFIX)-slack-signing-secret --data-file=- --project $(PROJECT_ID)

register-sheets-oauth: ## One-time: mint & store a Google Sheets OAuth refresh token for settings access
	@read -p "Path to OAuth client secret JSON (Desktop app, from GCP Console): " cs; \
	tmp=$$(mktemp); \
	trap 'rm -f $$tmp' EXIT; \
	uv run python scripts/get_sheets_oauth_token.py "$$cs" "$$tmp" || exit 1; \
	gcloud secrets create $(APP_PREFIX)-sheets-oauth --replication-policy="automatic" --project $(PROJECT_ID) || true; \
	gcloud secrets versions add $(APP_PREFIX)-sheets-oauth --data-file="$$tmp" --project $(PROJECT_ID); \
	echo "Stored OAuth credentials in secret $(APP_PREFIX)-sheets-oauth."
