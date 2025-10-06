"""
APR Analysis Orchestrator

This module contains the main orchestration logic for coordinating
multiple agents in the APR analysis system. It handles agent deployment,
analysis execution, and result synthesis.
"""

import time
from typing import Dict, List
from azure.ai.agents.models import MessageRole

from agents import create_pav_agent, create_ppa_agent, create_sup_agent, create_dup_agent, create_coordinator_agent
from agent_tools import (
    get_jira_ticket_description, get_pull_request_body, get_pull_request_title,
    get_control_plan_metrics_from_pr_comment, get_jira_ticket_title, 
    get_jira_ticket_release_notes, get_jira_ticket_xlsx_attachment, 
    get_jira_ticket_attachments, get_PRs_from_apr, get_feature_rankings,
    get_pav_metrics_for_apr, get_ppa_metrics_for_apr, 
    get_sup_metrics_for_apr, get_dup_metrics_for_apr, create_confluence_page
)


class APROrchestrator:
    """
    Main orchestrator for APR analysis workflow.
    
    This class coordinates the deployment and execution of multiple agents
    to perform comprehensive APR analysis with metric collection and synthesis.
    """
    
    def __init__(self, agents_client, model_deployment_name: str):
        """
        Initialize the orchestrator.
        
        Args:
            agents_client: Azure AI agents client
            model_deployment_name: Name of the model deployment
        """
        self.agents_client = agents_client
        self.model_deployment_name = model_deployment_name
        self.agents = {}
        self.threads = {}
        
        # Initialize agent instances using the creation functions
        self.agent_instances = {
            'pav': create_pav_agent(model_deployment_name),
            'ppa': create_ppa_agent(model_deployment_name),
            'sup': create_sup_agent(model_deployment_name),
            'dup': create_dup_agent(model_deployment_name),
            'coordinator': create_coordinator_agent(model_deployment_name)
        }
        
        # Enable auto function calls on initialization
        self._enable_auto_function_calls()
    
    def _enable_auto_function_calls(self):
        """Enable auto function calls for all agent tools."""
        all_tools = {
            get_jira_ticket_description, get_pull_request_body, get_pull_request_title,
            get_control_plan_metrics_from_pr_comment, get_jira_ticket_title, 
            get_jira_ticket_release_notes, get_jira_ticket_xlsx_attachment, 
            get_jira_ticket_attachments, get_PRs_from_apr, get_feature_rankings,
            get_pav_metrics_for_apr, get_ppa_metrics_for_apr, 
            get_sup_metrics_for_apr, get_dup_metrics_for_apr, create_confluence_page
        }
        self.agents_client.enable_auto_function_calls(all_tools)
    
    def create_agents(self) -> bool:
        """
        Create and deploy all agents.
        
        Returns:
            bool: True if all agents created successfully
        """
        print("🔧 Creating specialized agents...")
        
        try:
            # Create each agent using the agent instances
            for agent_type, agent_instance in self.agent_instances.items():
                self.agents[agent_type] = self.agents_client.create_agent(**agent_instance.to_create_params())
                print(f"✅ Created {agent_instance.name}")
            
            # Create threads for each agent
            for agent_type in self.agents.keys():
                self.threads[agent_type] = self.agents_client.threads.create()
            
            print(f"✅ Created {len(self.agents)} agents successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error creating agents: {e}")
            return False
    
    def run_metric_analysis(self, apr_number: str, agent_type: str, retries: int = 2) -> str:
        """
        Run analysis for a specific metric agent with retry logic.
        
        Args:
            apr_number: APR number to analyze
            agent_type: Type of agent (pav, ppa, sup, dup)
            retries: Number of retry attempts
            
        Returns:
            str: Analysis result
        """
        agent = self.agents[agent_type]
        thread = self.threads[agent_type]
        
        for attempt in range(retries + 1):
            try:
                if attempt > 0:
                    print(f"🔄 Retry {attempt}: Running {agent_type.upper()} analysis for APR {apr_number}...")
                else:
                    print(f"🔄 Running {agent_type.upper()} analysis for APR {apr_number}...")
                
                # Send message to the specific agent
                message = self.agents_client.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=f"Please analyze APR {apr_number} as per your instructions."
                )
                
                # Use the timeout from agent metadata
                timeout = self.agent_instances[agent_type].metadata.get("timeout", 360)
                run = self.agents_client.runs.create_and_process(
                    thread_id=thread.id,
                    agent_id=agent.id,
                    timeout=timeout
                )
                
                # Get the response
                messages = list(self.agents_client.messages.list(thread_id=thread.id))
                
                if messages and messages[0].role == MessageRole.AGENT:
                    result = messages[0].content[0].text.value
                    print(f"✅ {agent_type.upper()} analysis completed")
                    return result
                else:
                    if attempt < retries:
                        print(f"⚠️ No response from {agent_type.upper()} agent, retrying...")
                        time.sleep(5)  # Brief pause before retry
                        continue
                    else:
                        error_msg = f"❌ {agent_type.upper()} agent failed to provide analysis after {retries + 1} attempts"
                        print(error_msg)
                        return error_msg
                        
            except Exception as e:
                if attempt < retries:
                    print(f"⚠️ {agent_type.upper()} agent error: {e}, retrying...")
                    time.sleep(5)  # Brief pause before retry
                    continue
                else:
                    error_msg = f"❌ {agent_type.upper()} agent execution failed after {retries + 1} attempts: {e}"
                    print(error_msg)
                    return error_msg
    
    def create_final_report(self, apr_number: str, pav_result: str, ppa_result: str, 
                           sup_result: str, dup_result: str) -> str:
        """
        Use coordinator agent to create final comprehensive report.
        
        Args:
            apr_number: APR number being analyzed
            pav_result: PAV analysis result
            ppa_result: PPA analysis result  
            sup_result: SUP analysis result
            dup_result: DUP analysis result
            
        Returns:
            str: Final comprehensive report
        """
        print("🔄 Creating comprehensive final report...")
        
        coordinator = self.agents['coordinator']
        thread = self.threads['coordinator']
        
        # Provide data to coordinator without redundant instructions
        prompt = f"""Please analyze and synthesize the results for APR {apr_number}.

Here are the metric analysis findings from the specialized agents:

PAV AGENT ANALYSIS:
{pav_result}

PPA AGENT ANALYSIS:
{ppa_result}

SUP AGENT ANALYSIS:
{sup_result}

DUP AGENT ANALYSIS:
{dup_result}

Please create your comprehensive analysis following your instructions."""
        
        # Send to coordinator
        self.agents_client.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )
        
        # Process final report with extended timeout for JIRA analysis
        print("⏳ Coordinator analyzing patterns and linking JIRA tickets...")
        timeout = self.agent_instances['coordinator'].metadata.get("timeout", 600)
        run = self.agents_client.runs.create_and_process(
            thread_id=thread.id,
            agent_id=coordinator.id,
            timeout=timeout
        )
        
        # Get final report
        messages = list(self.agents_client.messages.list(thread_id=thread.id))
        if messages and messages[0].role == MessageRole.AGENT:
            final_report = messages[0].content[0].text.value
            print("✅ Comprehensive report completed")
            return final_report
        else:
            return "❌ Failed to generate comprehensive report"
    
    def analyze_apr(self, apr_number: str) -> str:
        """
        Run complete APR analysis across all metrics.
        
        Args:
            apr_number: APR number to analyze
            
        Returns:
            str: Final comprehensive report
        """
        print(f"\n🚀 Starting comprehensive APR {apr_number} analysis...")
        print("=" * 60)
        
        # Run all metric analyses
        results = {}
        metric_agents = ['pav', 'ppa', 'sup', 'dup']
        
        for agent_type in metric_agents:
            results[agent_type] = self.run_metric_analysis(apr_number, agent_type)
        
        # Create final comprehensive report
        final_report = self.create_final_report(
            apr_number, 
            results['pav'], 
            results['ppa'],
            results['sup'], 
            results['dup']
        )
        
        print("=" * 60)
        print(f"🎉 APR {apr_number} analysis complete!")
        return final_report
    
    def cleanup(self):
        """Clean up all deployed agents."""
        print("\n🧹 Cleaning up agents...")
        for agent_type, agent in self.agents.items():
            try:
                self.agents_client.delete_agent(agent.id)
                print(f"✅ Deleted {agent_type} agent")
            except Exception as e:
                print(f"⚠️ Error deleting {agent_type} agent: {e}")
        print("🎉 Cleanup completed")
    
    def get_agent_status(self) -> Dict[str, str]:
        """Get status of all agents."""
        return {
            agent_type: "deployed" if agent_type in self.agents else "not_deployed"
            for agent_type in self.agent_instances.keys()
        }