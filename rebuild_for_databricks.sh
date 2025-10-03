#!/bin/bash
# rebuild_for_databricks.sh - Simple rebuild script

set -e

echo "🔄 Rebuilding APR Analysis Wheel for Databricks"
echo "==============================================="

# Step 1: Clean previous builds
echo "🧹 Step 1: Cleaning previous build artifacts..."
rm -rf build/ dist/ *.egg-info/
echo "✅ Cleaned"

# Step 2: Show current version
echo "📋 Step 2: Current version info..."
python3 -c "
import re
with open('setup.py', 'r') as f:
    content = f.read()
    version_match = re.search(r'version=\"([^\"]+)\"', content)
    if version_match:
        print(f'Current version: {version_match.group(1)}')
    else:
        print('Version not found in setup.py')
"

# Step 3: Build new wheel
echo "🔧 Step 3: Building new wheel..."
python3 -m build --wheel

# Step 4: Show what was built
echo "📦 Step 4: Build results..."
ls -la dist/
echo ""

# Step 5: Quick validation
echo "🔍 Step 5: Quick validation..."
latest_wheel=$(ls -t dist/*.whl | head -n 1)
echo "Latest wheel: $(basename "$latest_wheel")"

# Check wheel size and basic metadata
wheel_size=$(ls -lh "$latest_wheel" | awk '{print $5}')
echo "Wheel size: $wheel_size"

# Test wheel contents
python3 -c "
import zipfile
with zipfile.ZipFile('$latest_wheel', 'r') as z:
    files = z.namelist()
    print(f'Files in wheel: {len(files)}')
    
    # Show main packages
    packages = set(f.split('/')[0] for f in files if '/' in f and not f.startswith('orbis_poi_control_plan_agents-'))
    print(f'Main packages: {sorted(packages)}')
"

echo ""
echo "✅ Rebuild complete!"
echo ""
echo "🚀 Next steps:"
echo "1. Upload to Databricks: $latest_wheel"
echo "2. In Databricks notebook: %pip install /path/to/$(basename "$latest_wheel")"
echo "3. Import and use: from orbis_poi_control_plan_agents import analyze_apr"