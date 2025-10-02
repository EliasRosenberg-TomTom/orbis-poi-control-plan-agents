import os
from azure.ai.projects import AIProj    def chat_mode(self):
        """Simple chat mode that works like the original."""
        print(f"\n🤖 APR Analysis System Ready!")
        print("💬 You're chatting with the APR Coordinator")
        print("📋 For APR analysis, just provide an APR number (e.g., '121' or 'analyze APR 121')")
        print("❓ For general questions, ask normally")
        print("🚪 Type 'exit' or 'quit' to end\n")
        
        # Get coordinator agent from the orchestrator
        coordinator_agent = self.orchestrator.agents['coordinator']
        coordinator_thread = self.orchestrator.threads['coordinator']
        
        while True:
            try:
                user_input = input("You: ").strip()
                if user_input.lower() in {"exit", "quit"}:
                    print("👋 Ending conversation...")
                    break
                    
                if not user_input:
                    continue
                
                # Check if user is requesting APR analysis
                import re
                apr_match = re.search(r'\b(\d{1,4})\b', user_input)
                
                if apr_match and any(keyword in user_input.lower() for keyword in 
                                   ['apr', 'analyze', 'analysis', 'report', 'metrics']):
                    # This looks like an APR analysis request
                    apr_number = apr_match.group(1)
                    print(f"\n🎯 Detected APR analysis request for APR {apr_number}")
                    
                    final_report = self.orchestrator.analyze_apr(apr_number)
                    print(f"\n📊 Final Report:\n")
                    print("=" * 80)
                    print(final_report)
                    print("=" * 80)
                    
                elif user_input.isdigit():
                    # Just a number - assume it's an APR number
                    apr_number = user_input
                    print(f"\n🎯 Running APR analysis for APR {apr_number}")
                    
                    final_report = self.orchestrator.analyze_apr(apr_number)
                    print(f"\n📊 Final Report:\n")
                    print("=" * 80)
                    print(final_report)
                    print("=" * 80)
                    
                else:
                    # Regular conversation - use coordinator directly
                    print("💭 Processing with coordinator...")
                    
                    self.agents_client.messages.create(
                        thread_id=coordinator_thread.id,
                        role="user",
                        content=user_input
                    )
                    
                    run = self.agents_client.runs.create_and_process(
                        thread_id=coordinator_thread.id,
                        agent_id=coordinator_agent.id
                    )
                    
                    messages = list(self.agents_client.messages.list(thread_id=coordinator_thread.id))
                    if messages and messages[0].role.value == 'agent':
                        response = messages[0].content[0].text.value
                        print(f"\n🤖 Coordinator: {response}\n")
                    else:
                        print("❌ Sorry, I didn't get a response. Please try again.\n")
                        
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                print("Please try again.\n")lient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Import new modular components
from orchestrator.orchestrator import APROrchestrator
from utils.chat_interface import ChatInterface
from utils.config import Config
from agent_tools import (
    get_jira_ticket_description, get_pull_request_body,
    get_control_plan_metrics_from_pr_comment, get_jira_ticket_title, 
    get_jira_ticket_release_notes, get_jira_ticket_attachments,
    get_jira_ticket_xlsx_attachment,
    get_pav_metrics_for_apr, get_ppa_metrics_for_apr, 
    get_sup_metrics_for_apr, get_dup_metrics_for_apr,
    get_PRs_from_apr, get_pull_request_title, get_feature_rankings
)

load_dotenv()


class LegacyManualOrchestration:
    def __init__(self, agents_client, model_deployment_name):
        """Initialize with new modular components."""
        self.agents_client = agents_client
        self.model_deployment_name = model_deployment_name
        
        # Use the new orchestrator
        self.orchestrator = APROrchestrator(agents_client, model_deployment_name)
        
        # Use the new chat interface 
        self.chat_interface = ChatInterface(agents_client, model_deployment_name)
        
        # Legacy compatibility properties
        self.agents = {}
        self.threads = {}
        
    def create_agents(self):
        """Create agents using the new orchestrator."""
        return self.orchestrator.create_agents()
    
    def analyze_apr(self, apr_number: str) -> str:
        """Analyze APR using the new orchestrator."""
        return self.orchestrator.analyze_apr(apr_number)
    
    def chat_mode(self):
        """Start chat mode using the new chat interface."""
        print("\n� Using new modular chat interface...")
        return self.chat_interface.start_chat_session()
    
    def cleanup(self):
        """Clean up agents using the new orchestrator."""
        return self.orchestrator.cleanup()

def main():
    
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
            get_sup_metrics_for_apr, get_dup_metrics_for_apr
        })
        
        model_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME")
        
        if model_deployment_name is None:
            print("❌ Error: Please define the environment variable MODEL_DEPLOYMENT_NAME.")
            return 1
        
        # Use the legacy wrapper (which delegates to new architecture)
        orchestrator = LegacyManualOrchestration(agents_client, model_deployment_name)
        
        try:
            # Deploy agents immediately
            print("🚀 Deploying agents...")
            orchestrator.create_agents()
            
            # Ask if user wants to chat
            choice = input("\n💬 Start interactive chat mode? (y/n): ").strip().lower()
            if choice in ['y', 'yes', '']:
                orchestrator.chat_mode()
            else:
                print("👍 Agents deployed and ready. You can run manual_orchestration.py again to start chatting.")
        except KeyboardInterrupt:
            print("\n👋 Interrupted by user")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            orchestrator.cleanup()
    
    return 0


if __name__ == "__main__":
    exit(main())