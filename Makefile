# Makefile - Simple utilities for APR Analysis System
# Main workflow: use ./quick_rebuild.sh for rebuilding wheels

.PHONY: clean test-cli test-imports install-local help

# Clean build artifacts (also done by quick_rebuild.sh)
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

# Test the CLI tool
test-cli:
	@echo "🧪 Testing CLI tool..."
	python3 manual_orchestration.py --help

# Test package imports
test-imports:
	@echo "🧪 Testing package imports..."
	python3 -c "from manual_orchestration import analyze_apr; print('✅ Import successful')"
	python3 -c "import pandas; print('✅ pandas:', pandas.__version__)"
	python3 -c "import numpy; print('✅ numpy:', numpy.__version__)"

# Install for local development
install-local:
	@echo "📦 Installing dependencies for local development..."
	pip install -r requirements-local.txt
	pip install -e .

# Show available commands
help:
	@echo "📋 Available commands:"
	@echo "  make clean       - Clean build artifacts"
	@echo "  make test-cli    - Test CLI functionality"  
	@echo "  make test-imports - Test package imports"
	@echo "  make install-local - Install for local development"
	@echo ""
	@echo "🚀 Main workflow:"
	@echo "  ./quick_rebuild.sh - Rebuild wheel for Databricks"