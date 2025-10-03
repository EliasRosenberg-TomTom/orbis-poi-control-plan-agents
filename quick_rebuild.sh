#!/bin/bash
# quick_rebuild.sh - Ultra-simple rebuild for after making changes

# Just the essentials - clean and rebuild
rm -rf build/ dist/ *.egg-info/
python3 -m build --wheel

# Show what was built
echo ""
echo "✅ New wheel ready:"
ls -lh dist/*.whl