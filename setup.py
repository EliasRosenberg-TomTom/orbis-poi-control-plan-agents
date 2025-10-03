from setuptools import setup, find_packages
import os

# Use Databricks-compatible requirements if available, fallback to regular requirements
requirements_file = 'requirements-databricks.txt' if os.path.exists('requirements-databricks.txt') else 'requirements.txt'

with open(requirements_file, 'r') as f:
    requirements = [
        line.strip() for line in f 
        if line.strip() and not line.startswith('#') and not line.startswith('-')
    ]

# Remove any problematic dependencies for Databricks
databricks_excluded = ['pandas', 'numpy', 'pyarrow', 'pyspark', 'black', 'pylint', 'ansible-core']
requirements = [req for req in requirements if not any(excluded in req.lower() for excluded in databricks_excluded)]

setup(
    name="orbis-poi-control-plan-agents",
    version="1.0.1",  # Increment version for Databricks compatibility
    description="APR Analysis System with Multi-Agent Architecture (Databricks Compatible)",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.8",
    include_package_data=True,
    package_data={
        '': ['*.csv', '*.txt', '*.yaml', '*.yml'],
    },
)