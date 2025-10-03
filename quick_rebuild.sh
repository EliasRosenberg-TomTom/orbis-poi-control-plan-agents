#!/bin/bash
# quick_rebuild.sh - Fast rebuild for Databricks after making changes

set -e

echo "🔄 Quick rebuild for Databricks..."

# Clean and rebuild
rm -rf build/ dist/ *.egg-info/
python3 -m build --wheel

# Show results
echo "✅ New wheel ready:"
ls -lh dist/*.whl