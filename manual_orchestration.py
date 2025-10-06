#!/usr/bin/env python3
"""
APR Analysis System - Command Line Tool

Simple CLI tool for analyzing APRs using multi-agent system.

Usage:
    python manual_orchestration.py <apr_number>
    
Examples:
    python manual_orchestration.py 123
    python manual_orchestration.py APR-456
"""

import os
import sys
import argparse
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Import new modular components
from orchestrator.orchestrator import APROrchestrator
from agent_tools import (
    get_jira_ticket_description, get_pull_request_body,
    get_control_plan_metrics_from_pr_comment, get_jira_ticket_title, 
    get_jira_ticket_release_notes, get_jira_ticket_attachments,
    get_jira_ticket_xlsx_attachment,
    get_pav_metrics_for_apr, get_ppa_metrics_for_apr, 
    get_sup_metrics_for_apr, get_dup_metrics_for_apr,
    get_PRs_from_apr, get_pull_request_title, get_feature_rankings, create_confluence_page
)

load_dotenv()


def format_apr_number(apr_input: str) -> str:
    """Format APR input to consistent format."""
    # Remove APR- prefix if present and just use the number
    if apr_input.upper().startswith('APR-'):
        return apr_input[4:]
    return apr_input


def analyze_apr(apr_number: str) -> int:
    """
    Analyze a single APR and return exit code.
    
    Args:
        apr_number: APR number to analyze
        
    Returns:
        int: 0 for success, 1 for error
    """
    print(f"🎯 Analyzing APR {apr_number}")
    print("=" * 50)
    
    # Initialize Azure AI Project client
    project_endpoint = os.environ.get("AZURE_EXISTING_AIPROJECT_ENDPOINT")
    if not project_endpoint:
        print("❌ Error: AZURE_EXISTING_AIPROJECT_ENDPOINT environment variable not set")
        return 1
    
    project_client = AIProjectClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential(),
    )
    
    with project_client:
        agents_client = project_client.agents
        
        # Enable auto function calls for all tools
        agents_client.enable_auto_function_calls({
            get_jira_ticket_description, get_pull_request_body, get_pull_request_title,
            get_control_plan_metrics_from_pr_comment, get_jira_ticket_title, 
            get_jira_ticket_release_notes, get_jira_ticket_xlsx_attachment, 
            get_jira_ticket_attachments, get_PRs_from_apr, get_feature_rankings,
            get_pav_metrics_for_apr, get_ppa_metrics_for_apr, 
            get_sup_metrics_for_apr, get_dup_metrics_for_apr  # create_confluence_page
        })
        
        model_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME")
        if model_deployment_name is None:
            print("❌ Error: Please define the environment variable MODEL_DEPLOYMENT_NAME.")
            return 1
        
        # Create the orchestrator
        orchestrator = APROrchestrator(agents_client, model_deployment_name)
        
        try:
            # Deploy agents
            orchestrator.create_agents()
            
            # Run analysis
            final_report = orchestrator.analyze_apr(apr_number)
            
            # Display results
            print(final_report)
            
        except KeyboardInterrupt:
            print("\n👋 Analysis interrupted by user")
            return 1
        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            return 1
        finally:
            print("\n🧹 Cleaning up agents...")
            orchestrator.cleanup()
    
    return 0


def main():
    """Main entry point for CLI tool."""
    parser = argparse.ArgumentParser(
        description="APR Analysis System - Analyze APRs using multi-agent system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 123          # Analyze APR 123
  %(prog)s APR-456      # Analyze APR 456
  %(prog)s 789          # Analyze APR 789
        """
    )
    
    parser.add_argument(
        'apr_number',
        help='APR number to analyze (with or without APR- prefix)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='APR Analysis System 1.0'
    )
    
    # Parse arguments
    if len(sys.argv) == 1:
        parser.print_help()
        return 1
        
    args = parser.parse_args()
    
    # Format and analyze APR
    formatted_apr = format_apr_number(args.apr_number)
    exit_code = analyze_apr(formatted_apr)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())