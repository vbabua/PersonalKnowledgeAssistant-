.PHONY: run-notion-to-vector run-notion-to-vector-nocache

run-notion-to-vector:
	@echo "🚀 Running Notion to Vector pipeline with config..."
	python run.py

run-notion-to-vector-nocache:
	@echo "🚀 Running Notion to Vector pipeline with config and no cache..."
	python run.py --no-cache