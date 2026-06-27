.PHONY: template help

template: ## Generate a template CSV for user settings
	@echo "slack_user_id,jobcan_company_id,jobcan_staff_code,morning_off_start,morning_off_end,afternoon_off_start,afternoon_off_end,working_hours_start,working_hours_end,timezone" > user_settings_template.csv
	@echo "U01234567,1234,staff-001,09:00,13:00,14:00,18:00,09:00,18:00,Asia/Tokyo" >> user_settings_template.csv
	@echo "Created user_settings_template.csv"
	@echo "Instruction: Upload this to Google Sheets and use the sheet ID in your Terraform config."

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
