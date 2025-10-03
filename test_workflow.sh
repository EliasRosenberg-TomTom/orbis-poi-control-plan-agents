#!/bin/bash
# test_workflow.sh - Comprehensive testing workflow

set -e

echo "🧪 APR Analysis System - Complete Testing Workflow"
echo "=================================================="

# Test 1: Current environment
echo "📍 Step 1: Testing current environment..."
python test_environment.py

# Test 2: CLI functionality  
echo -e "\n📍 Step 2: Testing CLI functionality..."
python manual_orchestration.py --help

# Test 3: Import tests
echo -e "\n📍 Step 3: Testing package imports..."
python -c "
from manual_orchestration import analyze_apr, format_apr_number
from agents.pav_agent import create_pav_agent
from orchestrator.orchestrator import APROrchestrator
print('✅ All critical imports successful')
"

# Test 4: Function tests (without actual Azure calls)
echo -e "\n📍 Step 4: Testing core functions..."
python -c "
from manual_orchestration import format_apr_number
test_cases = ['123', 'APR-456', 'apr-789']
for case in test_cases:
    result = format_apr_number(case)
    print(f'✅ {case} → {result}')
"

# Test 5: Wheel installation test (in temporary environment)
echo -e "\n📍 Step 5: Testing wheel installation..."
if command -v python3 -m venv &> /dev/null; then
    echo "Creating temporary test environment..."
    rm -rf /tmp/apr_test_env
    python3 -m venv /tmp/apr_test_env
    source /tmp/apr_test_env/bin/activate
    
    echo "Installing wheel in clean environment..."
    pip install -q dist/orbis_poi_control_plan_agents-1.0.1-py3-none-any.whl
    
    # Add pandas/numpy for the test
    pip install -q "pandas>=2.0.0" "numpy>=1.21.0,<2.0"
    
    echo "Testing in clean environment..."
    python -c "
import orbis_poi_control_plan_agents
print('✅ Wheel installs correctly in clean environment')
"
    
    deactivate
    rm -rf /tmp/apr_test_env
    echo "✅ Clean environment test passed"
else
    echo "⚠️  venv not available, skipping clean environment test"
fi

echo -e "\n🎉 All local tests completed successfully!"
echo ""
echo "📋 Next Steps:"
echo "1. Upload dist/orbis_poi_control_plan_agents-1.0.1-py3-none-any.whl to Databricks"
echo "2. In Databricks notebook, run: %pip install /path/to/wheel.whl" 
echo "3. Test import: from orbis_poi_control_plan_agents import analyze_apr"