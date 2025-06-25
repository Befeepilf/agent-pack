install:
	@command -v uv >/dev/null 2>&1 || { echo "uv is not installed. Installing uv..."; curl -LsSf https://astral.sh/uv/0.6.12/install.sh | sh; source ~/.bashrc; }
	uv sync --dev --extra jupyter --frozen

test:
	uv run pytest tests/unit && uv run pytest tests/integration

playground:
	@echo "==============================================================================="
	@echo "| 🚀 Starting your agent playground...                                        |"
	@echo "|                                                                             |"
	@echo "| 💡 Try asking: How to save a pandas dataframe to CSV?                       |"
	@echo "|                                                                             |"
	@echo "| 🔍 IMPORTANT: Select the 'app' folder to interact with your agent.          |"
	@echo "==============================================================================="
	uv run adk web --port 8501

backend:
	# Export dependencies to requirements file using uv export.
	uv export --no-hashes --no-header --no-dev --no-emit-project --no-annotate --frozen > .requirements.txt 2>/dev/null || \
	uv export --no-hashes --no-header --no-dev --no-emit-project --frozen > .requirements.txt && uv run app/agent_engine_app.py

setup-dev-env:
	PROJECT_ID=$$(gcloud config get-value project) && \
	(cd deployment/terraform/dev && terraform init && terraform apply --var-file vars/env.tfvars --var dev_project_id=$$PROJECT_ID --auto-approve)

data-ingestion:
	PROJECT_ID=$$(gcloud config get-value project) && \
	(cd data_ingestion && uv run data_ingestion_pipeline/submit_pipeline.py \
		--project-id=$$PROJECT_ID \
		--region="europe-west3" \
		--data-store-id="agent-123-datastore" \
		--data-store-region="eu" \
		--service-account="agent-123-rag@$$PROJECT_ID.iam.gserviceaccount.com" \
		--pipeline-root="gs://$$PROJECT_ID-agent-123-rag" \
		--pipeline-name="data-ingestion-pipeline")

lint:
	uv run codespell
	uv run ruff check . --diff
	uv run ruff format . --check --diff
	uv run mypy .
