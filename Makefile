# Makefile for managing different environments and builds

.PHONY: install-local install-databricks build-local build-databricks test clean

# Local development setup
install-local:
	@echo "📦 Installing dependencies for local development..."
	pip install -r requirements-local.txt
	pip install -e .

# Install databricks-compatible wheel locally for testing
install-databricks-wheel:
	@echo "📦 Installing Databricks-compatible wheel locally..."
	pip install dist/orbis_poi_control_plan_agents-1.0.1-py3-none-any.whl
	pip install pandas numpy  # Add back essential packages

# Build wheel for local development (includes all dependencies)
build-local:
	@echo "🔧 Building wheel for local development..."
	@if [ -f "requirements-local.txt" ]; then \
		cp requirements-local.txt requirements.txt; \
	fi
	@sed -i.bak 's/requirements-databricks.txt/requirements.txt/' setup.py
	python -m build --wheel
	@mv requirements.txt.bak requirements.txt 2>/dev/null || true
	@echo "✅ Local wheel built: dist/orbis_poi_control_plan_agents-*-py3-none-any.whl"

# Build wheel for Databricks (minimal dependencies)
build-databricks:
	@echo "🔧 Building wheel for Databricks..."
	python -m build --wheel
	@echo "✅ Databricks wheel built: dist/orbis_poi_control_plan_agents-*-py3-none-any.whl"

# Run local tests
test:
	@echo "🧪 Running tests locally..."
	python -m pytest tests/ -v --cov=.

# Test the CLI tool locally
test-cli:
	@echo "🧪 Testing CLI tool locally..."
	python manual_orchestration.py --help

# Test imports
test-imports:
	@echo "🧪 Testing package imports..."
	python -c "from manual_orchestration import analyze_apr; print('✅ Import successful')"
	python -c "import pandas; print('✅ pandas:', pandas.__version__)"
	python -c "import numpy; print('✅ numpy:', numpy.__version__)"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

# Full local development setup
setup-local: clean install-local build-local test-imports
	@echo "🎉 Local development environment ready!"

# Full Databricks deployment prep
setup-databricks: clean build-databricks
	@echo "🎉 Databricks wheel ready for upload!"