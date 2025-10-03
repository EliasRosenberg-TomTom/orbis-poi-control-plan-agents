#!/usr/bin/env python3
"""
Environment Test Script

Tests the APR analysis system in different environments to ensure compatibility.
"""

import sys
import subprocess
import importlib.util
from pathlib import Path

def test_environment():
    """Test the current Python environment for compatibility."""
    print("🔍 Environment Testing Report")
    print("=" * 50)
    
    # Test Python version
    print(f"🐍 Python Version: {sys.version}")
    
    # Test critical imports
    critical_packages = [
        ('pandas', 'Data processing'),
        ('numpy', 'Numerical computing'),
        ('azure.ai.projects', 'Azure AI Projects'),
        ('azure.identity', 'Azure Authentication'),
    ]
    
    missing_packages = []
    
    for package, description in critical_packages:
        try:
            module = importlib.import_module(package)
            version = getattr(module, '__version__', 'Unknown')
            print(f"✅ {package}: {version} - {description}")
        except ImportError as e:
            print(f"❌ {package}: MISSING - {description}")
            missing_packages.append(package)
    
    # Test our package
    try:
        from manual_orchestration import analyze_apr, format_apr_number
        print("✅ APR Analysis Package: Available")
        
        # Test basic functionality
        formatted = format_apr_number("APR-123")
        print(f"✅ Package Functions: Working (test: APR-123 → {formatted})")
        
    except ImportError as e:
        print(f"❌ APR Analysis Package: {e}")
        missing_packages.append('manual_orchestration')
    
    # Environment recommendations
    print("\n📋 Environment Status:")
    if not missing_packages:
        print("🎉 Environment is fully compatible!")
        return True
    else:
        print("⚠️  Missing packages detected:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        
        print("\n🔧 Recommended Actions:")
        if any(pkg in ['pandas', 'numpy'] for pkg in missing_packages):
            print("   For local development:")
            print("   pip install -r requirements-local.txt")
        
        if 'manual_orchestration' in missing_packages:
            print("   Install the package:")
            print("   pip install -e .")
        
        return False

def test_wheel_compatibility():
    """Test wheel file compatibility."""
    print("\n🎯 Wheel Compatibility Test")
    print("=" * 30)
    
    wheel_path = Path("dist").glob("orbis_poi_control_plan_agents-*.whl")
    wheel_files = list(wheel_path)
    
    if not wheel_files:
        print("❌ No wheel files found. Run 'make build-databricks' or 'make build-local'")
        return False
    
    latest_wheel = max(wheel_files, key=lambda p: p.stat().st_mtime)
    print(f"📦 Latest wheel: {latest_wheel.name}")
    
    # Check wheel metadata
    try:
        import zipfile
        with zipfile.ZipFile(latest_wheel, 'r') as z:
            metadata_files = [f for f in z.namelist() if f.endswith('METADATA')]
            if metadata_files:
                metadata = z.read(metadata_files[0]).decode()
                requires = [line.split(':')[-1].strip() 
                          for line in metadata.split('\n') 
                          if line.startswith('Requires-Dist:')]
                
                print(f"📋 Dependencies in wheel:")
                for req in requires[:5]:  # Show first 5
                    print(f"   - {req}")
                if len(requires) > 5:
                    print(f"   ... and {len(requires) - 5} more")
                
                # Check for problematic dependencies
                problematic = ['pandas', 'numpy>=2', 'pyarrow']
                found_problematic = [req for req in requires if any(p in req.lower() for p in problematic)]
                
                if found_problematic:
                    print("⚠️  Potentially problematic dependencies found:")
                    for dep in found_problematic:
                        print(f"   - {dep}")
                else:
                    print("✅ No problematic dependencies detected")
                
    except Exception as e:
        print(f"❌ Could not analyze wheel: {e}")
        return False
    
    return True

def suggest_environment_setup():
    """Suggest proper environment setup based on current state."""
    print("\n🎯 Environment Setup Recommendations")
    print("=" * 40)
    
    print("For LOCAL DEVELOPMENT:")
    print("1. make setup-local")
    print("   - Installs all dependencies including pandas/numpy")
    print("   - Builds local-compatible wheel")
    print("   - Runs tests")
    
    print("\nFor DATABRICKS DEPLOYMENT:")
    print("1. make setup-databricks") 
    print("   - Builds minimal wheel without pandas/numpy")
    print("   - Ready for Databricks upload")
    
    print("\nFor TESTING BOTH ENVIRONMENTS:")
    print("1. make test-imports  # Test current environment")
    print("2. make test-cli      # Test CLI functionality")
    
    print("\n📁 File Usage Guide:")
    print("- requirements-local.txt    → Local development")
    print("- requirements-databricks.txt → Databricks deployment")
    print("- requirements.txt         → Current active (symlinked)")

if __name__ == "__main__":
    print("🧪 APR Analysis System - Environment Compatibility Test\n")
    
    env_ok = test_environment()
    wheel_ok = test_wheel_compatibility()
    
    if env_ok and wheel_ok:
        print("\n🎉 All tests passed! Environment is ready.")
        sys.exit(0)
    else:
        print("\n⚠️  Issues detected. See recommendations below:")
        suggest_environment_setup()
        sys.exit(1)