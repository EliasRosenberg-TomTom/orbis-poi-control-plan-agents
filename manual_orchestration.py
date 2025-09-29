import os
import time
from typing import Dict, Optional

from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ToolSet, FunctionTool, MessageRole
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from agent_tools import (
    get_jira_ticket_description, get_pull_request_body,
    get_control_plan_metrics_from_pr_comment, get_jira_ticket_title, 
    get_jira_ticket_release_notes, get_jira_ticket_attachments,
    get_jira_ticket_xlsx_attachment,
    get_pav_metrics_for_apr, 
    get_ppa_metrics_for_apr, 
    get_sup_metrics_for_apr, 
    get_dup_metrics_for_apr,
    get_PRs_from_apr, get_pull_request_title, get_feature_rankings
)

load_dotenv()

project_endpoint = os.environ["AZURE_EXISTING_AIPROJECT_ENDPOINT"]
model_name = os.environ["MODEL_DEPLOYMENT_NAME"]

project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential(),
)

class ManualOrchestration:
    def __init__(self, agents_client, model_deployment_name):
        self.agents_client = agents_client
        self.model_deployment_name = model_deployment_name
        self.agents = {}
        self.threads = {}
        
        # General tools for the coordinator (includes JIRA correlation tools)
        self.general_function_set = {
            get_jira_ticket_description, get_pull_request_body, get_pull_request_title,
            get_control_plan_metrics_from_pr_comment, get_jira_ticket_title, 
            get_jira_ticket_release_notes, get_jira_ticket_xlsx_attachment, 
            get_jira_ticket_attachments, get_PRs_from_apr, get_feature_rankings
        }
        
    def create_agents(self):
        """Create all 5 agents: PAV, PPA, SUP, DUP, and Coordinator"""
        print("🔧 Creating specialized metric agents...")
        
        # Create PAV agent with JIRA/PR correlation tools
        pav_functions = FunctionTool(functions={
            get_pav_metrics_for_apr, get_PRs_from_apr, get_pull_request_title, 
            get_jira_ticket_title, get_jira_ticket_description, get_feature_rankings
        })
        self.agents['pav'] = self.agents_client.create_agent(
            model=self.model_deployment_name,
            name="PAV_Agent",
            instructions="""You are the PAV Agent, a Map and Geospatial expert specialized in POI Availability (PAV) metrics analysis with JIRA correlation capability.
            
            WORKFLOW FOR APR ANALYSIS:
            1. **First call get_feature_rankings()** to get feature importance rankings
            2. **Call get_pav_metrics_for_apr()** to fetch PAV metric data  
            3. **Call get_PRs_from_apr()** to get all PRs for correlation analysis
            4. **For significant patterns, correlate with JIRA tickets using PR tools**
            
            ANALYSIS PRIORITIES (using feature rankings):
            - **High-ranked features take priority** over percentage magnitude
            - Small changes in critical PAV features (airports, hospitals) more important than large changes in low-ranked features
            - Complex percentages (large samples) preferred over round numbers (50%, 100% = low coverage)
            - Show improvements first, then drops
            
            PATTERN ANALYSIS:
            - Focus on patterns by country and definitiontag in validation_key
            - Prioritize multi-country patterns in same category  
            - Prioritize single countries affected across multiple categories
            - Structure: country/region → PAV impact → affected category
            
            JIRA CORRELATION:
            - For each significant PAV pattern, check PRs for semantic matches
            - **Conservative linking only**: match countries/categories in validation_key with PR/JIRA content
            - Use get_pull_request_title() and get_jira_ticket_title/description() for correlation
            - Include MPOI ticket numbers when correlations found
            
            OUTPUT FORMAT:
            - Bullet points for each pattern with metrics backing
            - Include JIRA correlations: • [Country] → [PAV Impact] → [Category] ([MPOI-XXXX: Title] if correlated)
            - Always mention total rows analyzed
            - Focus exclusively on PAV metrics""",
            tools=pav_functions.definitions
        )
        
        # Create PPA agent with JIRA/PR correlation tools
        ppa_functions = FunctionTool(functions={
            get_ppa_metrics_for_apr, get_PRs_from_apr, get_pull_request_title,
            get_jira_ticket_title, get_jira_ticket_description, get_feature_rankings
        })
        self.agents['ppa'] = self.agents_client.create_agent(
            model=self.model_deployment_name,
            name="PPA_Agent",
            instructions="""You are the PPA Agent, a Map and Geospatial expert specialized in POI Positional Accuracy (PPA) metrics analysis with JIRA correlation capability.
            
            WORKFLOW FOR APR ANALYSIS:
            1. **First call get_feature_rankings()** to get feature importance rankings
            2. **Call get_ppa_metrics_for_apr()** to fetch PPA metric data
            3. **Call get_PRs_from_apr()** to get all PRs for correlation analysis  
            4. **For significant patterns, correlate with JIRA tickets using PR tools**
            
            ANALYSIS PRIORITIES (using feature rankings):
            - **High-ranked features take priority** over percentage magnitude
            - Small accuracy changes in critical PPA features more important than large changes in low-ranked features
            - Complex percentages (large samples) preferred over round numbers (50%, 100% = low coverage)
            - Show accuracy improvements first, then degradations
            
            PATTERN ANALYSIS:
            - Focus on patterns by country and definitiontag in validation_key
            - Prioritize multi-country accuracy patterns in same category
            - Prioritize single countries with accuracy issues across multiple categories
            - Structure: country/region → PPA impact → affected category
            
            JIRA CORRELATION:
            - For each significant PPA pattern, check PRs for semantic matches
            - **Conservative linking only**: match countries/categories in validation_key with PR/JIRA content  
            - Look for keywords related to positioning, accuracy, coordinates, geocoding
            - Include MPOI ticket numbers when correlations found
            
            OUTPUT FORMAT:
            - Bullet points for each pattern with accuracy metrics backing
            - Include JIRA correlations: • [Country] → [PPA Impact] → [Category] ([MPOI-XXXX: Title] if correlated)
            - Always mention total rows analyzed
            - Focus exclusively on PPA metrics""",
            tools=ppa_functions.definitions
        )
        
        # Create SUP agent with JIRA/PR correlation tools
        sup_functions = FunctionTool(functions={
            get_sup_metrics_for_apr, get_PRs_from_apr, get_pull_request_title,
            get_jira_ticket_title, get_jira_ticket_description, get_feature_rankings
        })
        self.agents['sup'] = self.agents_client.create_agent(
            model=self.model_deployment_name,
            name="SUP_Agent", 
            instructions="""You are the SUP Agent, a Map and Geospatial expert specialized in Superfluous (SUP) metrics analysis with JIRA correlation capability.
            
            WORKFLOW FOR APR ANALYSIS:
            1. **First call get_feature_rankings()** to get feature importance rankings
            2. **Call get_sup_metrics_for_apr()** to fetch SUP metric data
            3. **Call get_PRs_from_apr()** to get all PRs for correlation analysis
            4. **For significant patterns, correlate with JIRA tickets using PR tools**
            
            ANALYSIS PRIORITIES (using feature rankings):
            - **High-ranked features take priority** over percentage magnitude  
            - Small SUP changes in critical features more important than large changes in low-ranked features
            - Complex percentages (large samples) preferred over round numbers (50%, 100% = low coverage)
            - Show superfluous reductions first (improvements), then increases (problems)
            
            PATTERN ANALYSIS:
            - Focus on patterns by country and definitiontag in validation_key
            - Prioritize multi-country superfluous patterns in same category
            - Prioritize single countries with superfluous issues across multiple categories
            - Structure: country/region → SUP impact → affected category
            
            JIRA CORRELATION:
            - For each significant SUP pattern, check PRs for semantic matches
            - **Conservative linking only**: match countries/categories in validation_key with PR/JIRA content
            - Look for keywords related to data cleanup, filtering, quality improvements
            - Include MPOI ticket numbers when correlations found
            
            OUTPUT FORMAT:
            - Bullet points for each pattern with SUP metrics backing
            - Include JIRA correlations: • [Country] → [SUP Impact] → [Category] ([MPOI-XXXX: Title] if correlated)
            - Always mention total rows analyzed
            - Focus exclusively on SUP metrics""",
            tools=sup_functions.definitions
        )
        
        # Create DUP agent with JIRA/PR correlation tools
        dup_functions = FunctionTool(functions={
            get_dup_metrics_for_apr, get_PRs_from_apr, get_pull_request_title,
            get_jira_ticket_title, get_jira_ticket_description, get_feature_rankings
        })
        self.agents['dup'] = self.agents_client.create_agent(
            model=self.model_deployment_name,
            name="DUP_Agent",
            instructions="""You are the DUP Agent, a Map and Geospatial expert specialized in Duplicate (DUP) metrics analysis with JIRA correlation capability.
            
            WORKFLOW FOR APR ANALYSIS:
            1. **First call get_feature_rankings()** to get feature importance rankings
            2. **Call get_dup_metrics_for_apr()** to fetch DUP metric data
            3. **Call get_PRs_from_apr()** to get all PRs for correlation analysis
            4. **For significant patterns, correlate with JIRA tickets using PR tools**
            
            ANALYSIS PRIORITIES (using feature rankings):
            - **High-ranked features take priority** over percentage magnitude
            - Small DUP changes in critical features more important than large changes in low-ranked features
            - Complex percentages (large samples) preferred over round numbers (50%, 100% = low coverage)
            - Show duplicate reductions first (improvements), then increases (problems)
            
            PATTERN ANALYSIS:
            - Focus on patterns by country and definitiontag in validation_key
            - Prioritize multi-country duplicate patterns in same category
            - Prioritize single countries with duplicate issues across multiple categories
            - Structure: country/region → DUP impact → affected category
            
            JIRA CORRELATION:
            - For each significant DUP pattern, check PRs for semantic matches
            - **Conservative linking only**: match countries/categories in validation_key with PR/JIRA content
            - Look for keywords related to deduplication, duplicate detection, data merging
            - Include MPOI ticket numbers when correlations found
            
            OUTPUT FORMAT:
            - Bullet points for each pattern with DUP metrics backing
            - Include JIRA correlations: • [Country] → [DUP Impact] → [Category] ([MPOI-XXXX: Title] if correlated)
            - Always mention total rows analyzed
            - Focus exclusively on DUP metrics""",
            tools=dup_functions.definitions
        )
        
        # Create Coordinator agent with full analysis workflow capability
        general_functions = FunctionTool(functions=self.general_function_set)
        self.agents['coordinator'] = self.agents_client.create_agent(
            model=self.model_deployment_name,
            name="APR_Coordinator",
            instructions="""You are the APR Analysis Coordinator, an expert in synthesizing multi-agent analysis into comprehensive release notes.

            WORKFLOW FOR APR SYNTHESIS:
            1. **Call get_feature_rankings()** to get feature importance context
            2. **Call get_PRs_from_apr()** to scan for BigRun PRs
            3. **Receive and synthesize analyses from PAV, PPA, SUP, DUP agents** (they handle their own JIRA correlations)
            4. **Focus on cross-metric patterns and BigRun detection**

            SYNTHESIS RESPONSIBILITIES:
            - **Cross-metric pattern detection**: Look for themes across PAV/PPA/SUP/DUP findings
            - **Feature ranking prioritization**: Use rankings to order importance of findings
            - **BigRun PR detection**: Exhaustively scan for 'conf(BR):' prefixed PRs
            - **Release note structuring**: Organize individual agent findings into coherent narrative
            
            BIGRUN PR DETECTION:
            - **Exhaustively scan ALL PRs** (direct and bundled) for 'conf(BR):' prefix
            - Include bundled PRs from daily rollups/RCs
            - List ALL BigRun PRs in dedicated section with full titles

            OUTPUT FORMAT (markdown):
            ```
            # APR [NUMBER] Release Notes

            ## Feature Rankings Context
            [Top 10 ranked features for priority context]

            ## Key Improvements (by Priority)
            [Synthesized improvements from all agents, ordered by feature ranking]
            • PAV: [findings with JIRA correlations from agent]
            • PPA: [findings with JIRA correlations from agent]
            • SUP: [findings with JIRA correlations from agent]
            • DUP: [findings with JIRA correlations from agent]

            ## Key Issues (by Priority)
            [Synthesized issues from all agents, ordered by feature ranking]

            ## Cross-Metric Patterns
            [Patterns spanning multiple metric types - your unique synthesis]
            
            ## BigRun PRs Included
            [All conf(BR): PRs with full titles]
            ```

            SYNTHESIS STANDARDS:
            - **Don't duplicate JIRA correlation** - agents provide that
            - **Focus on cross-cutting themes** across metric types
            - **Prioritize by feature rankings** not percentage magnitude
            - **Identify multi-country or multi-category patterns**
            - **Maintain quantitative focus** with agent-provided data
            - **Be the orchestrator, not the analyzer**

            You are conversational for general questions but follow this synthesis methodology for APR coordination.""",
            tools=general_functions.definitions
        )
        
        # Create threads for each agent
        for agent_type in self.agents.keys():
            self.threads[agent_type] = self.agents_client.threads.create()
            
        print(f"✅ Created {len(self.agents)} agents successfully")
        
    def run_metric_analysis(self, apr_number: str, agent_type: str) -> str:
        """Run analysis for a specific metric agent"""
        agent = self.agents[agent_type]
        thread = self.threads[agent_type]
        
        print(f"🔄 Running {agent_type.upper()} analysis for APR {apr_number}...")
        
        # Send message to the specific agent
        self.agents_client.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"Please analyze APR {apr_number} using your specialized metric analysis function."
        )
        
        # Process the analysis
        run = self.agents_client.runs.create_and_process(
            thread_id=thread.id,
            agent_id=agent.id
        )
        
        # Get the response
        messages = list(self.agents_client.messages.list(thread_id=thread.id))
        if messages and messages[0].role == MessageRole.AGENT:
            result = messages[0].content[0].text.value
            print(f"✅ {agent_type.upper()} analysis completed ({len(result)} characters)")
            return result
        else:
            error_msg = f"❌ {agent_type.upper()} agent failed to provide analysis"
            print(error_msg)
            return error_msg
            
    def create_final_report(self, apr_number: str, pav_result: str, ppa_result: str, 
                           sup_result: str, dup_result: str) -> str:
        """Use coordinator agent to create final comprehensive report"""
        print("🔄 Creating comprehensive final report...")
        
        coordinator = self.agents['coordinator']
        thread = self.threads['coordinator']
        
        # Create comprehensive prompt with all results
        prompt = f"""Please create a comprehensive APR {apr_number} analysis report using the following individual metric analyses:

PAV AGENT ANALYSIS:
{pav_result}

PPA AGENT ANALYSIS:
{ppa_result}

SUP AGENT ANALYSIS:
{sup_result}

DUP AGENT ANALYSIS:
{dup_result}

Please synthesize these into a professional markdown report with the structure specified in your instructions."""
        
        # Send to coordinator
        self.agents_client.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )
        
        # Process final report
        run = self.agents_client.runs.create_and_process(
            thread_id=thread.id,
            agent_id=coordinator.id
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
        """Run complete APR analysis across all metrics"""
        print(f"\n🚀 Starting comprehensive APR {apr_number} analysis...")
        print("=" * 60)
        
        # Run all metric analyses in parallel concept (sequential for now, could be parallelized)
        results = {}
        
        # Collect all individual analyses
        results['pav'] = self.run_metric_analysis(apr_number, 'pav')
        results['ppa'] = self.run_metric_analysis(apr_number, 'ppa') 
        results['sup'] = self.run_metric_analysis(apr_number, 'sup')
        results['dup'] = self.run_metric_analysis(apr_number, 'dup')
        
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
        
    def chat_mode(self):
        """Interactive chat mode"""
        coordinator = self.agents['coordinator']
        thread = self.threads['coordinator']
        
        print(f"\n🤖 APR Analysis System Ready!")
        print("💬 You're chatting with the APR Coordinator")
        print("📋 For APR analysis, just provide an APR number (e.g., '121' or 'analyze APR 121')")
        print("❓ For general questions, ask normally")
        print("🚪 Type 'exit' or 'quit' to end\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                if user_input.lower() in {"exit", "quit"}:
                    print("👋 Ending conversation...")
                    break
                    
                if not user_input:
                    continue
                
                # Check if user is requesting APR analysis
                # Simple detection - look for numbers that could be APR numbers
                import re
                apr_match = re.search(r'\b(\d{1,4})\b', user_input)
                
                if apr_match and any(keyword in user_input.lower() for keyword in 
                                   ['apr', 'analyze', 'analysis', 'report', 'metrics']):
                    # This looks like an APR analysis request
                    apr_number = apr_match.group(1)
                    print(f"\n🎯 Detected APR analysis request for APR {apr_number}")
                    
                    final_report = self.analyze_apr(apr_number)
                    print(f"\n📊 Final Report:\n")
                    print("=" * 80)
                    print(final_report)
                    print("=" * 80)
                    
                elif user_input.isdigit():
                    # Just a number - assume it's an APR number
                    apr_number = user_input
                    print(f"\n🎯 Running APR analysis for APR {apr_number}")
                    
                    final_report = self.analyze_apr(apr_number)
                    print(f"\n📊 Final Report:\n")
                    print("=" * 80)
                    print(final_report)
                    print("=" * 80)
                    
                else:
                    # Regular conversation - use coordinator
                    print("💭 Processing with coordinator...")
                    
                    self.agents_client.messages.create(
                        thread_id=thread.id,
                        role="user",
                        content=user_input
                    )
                    
                    run = self.agents_client.runs.create_and_process(
                        thread_id=thread.id,
                        agent_id=coordinator.id
                    )
                    
                    messages = list(self.agents_client.messages.list(thread_id=thread.id))
                    if messages and messages[0].role == MessageRole.AGENT:
                        response = messages[0].content[0].text.value
                        print(f"\n🤖 Coordinator: {response}\n")
                    else:
                        print("❌ Sorry, I didn't get a response. Please try again.\n")
                        
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                print("Please try again.\n")
    
    def cleanup(self):
        """Delete all agents"""
        print("\n🧹 Cleaning up agents...")
        for agent_type, agent in self.agents.items():
            try:
                self.agents_client.delete_agent(agent.id)
                print(f"✅ Deleted {agent_type} agent")
            except Exception as e:
                print(f"⚠️ Error deleting {agent_type} agent: {e}")
        print("🎉 Cleanup completed")

# Main execution
if __name__ == "__main__":
    with project_client:
        agents_client = project_client.agents
        
        # Enable auto function calls
        agents_client.enable_auto_function_calls({
            get_jira_ticket_description, get_pull_request_body, get_pull_request_title,
            get_control_plan_metrics_from_pr_comment, get_jira_ticket_title, 
            get_jira_ticket_release_notes, get_jira_ticket_xlsx_attachment, 
            get_jira_ticket_attachments, get_PRs_from_apr, get_feature_rankings,
            get_pav_metrics_for_apr, get_ppa_metrics_for_apr, 
            get_sup_metrics_for_apr, get_dup_metrics_for_apr
        })
        
        model_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME")
        
        if model_deployment_name is not None:
            orchestrator = ManualOrchestration(agents_client, model_deployment_name)
            
            try:
                orchestrator.create_agents()
                orchestrator.chat_mode()
            finally:
                orchestrator.cleanup()
        else:
            print("❌ Error: Please define the environment variable MODEL_DEPLOYMENT_NAME.")