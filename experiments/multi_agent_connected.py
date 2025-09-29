import os
import time
from typing import Set

from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ToolSet, FunctionTool, MessageRole, ConnectedAgentTool


from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from agent_tools import (get_jira_ticket_description, get_pull_request_body,
get_control_plan_metrics_from_pr_comment, get_jira_ticket_title, 
get_jira_ticket_release_notes, get_jira_ticket_attachments,
 get_jira_ticket_xlsx_attachment,
 get_pav_metrics_for_apr, 
 get_ppa_metrics_for_apr, 
 get_sup_metrics_for_apr, 
 get_dup_metrics_for_apr,
 get_PRs_from_apr, get_pull_request_title)

load_dotenv()

project_endpoint = os.environ["AZURE_EXISTING_AIPROJECT_ENDPOINT"]
model_name = os.environ["MODEL_DEPLOYMENT_NAME"]

project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential(),
)

# Function set for the team leader (includes general tools)
team_leader_function_set: Set = {
    get_jira_ticket_description, get_pull_request_body, get_pull_request_title,
    get_control_plan_metrics_from_pr_comment, get_jira_ticket_title, 
    get_jira_ticket_release_notes, get_jira_ticket_xlsx_attachment, 
    get_jira_ticket_attachments, get_PRs_from_apr
}

with project_client:
    agents_client = project_client.agents
    
    # Enable auto function calls for all functions
    agents_client.enable_auto_function_calls({
        get_jira_ticket_description, get_pull_request_body, get_pull_request_title,
        get_control_plan_metrics_from_pr_comment, get_jira_ticket_title, 
        get_jira_ticket_release_notes, get_jira_ticket_xlsx_attachment, 
        get_jira_ticket_attachments, get_PRs_from_apr,
        get_pav_metrics_for_apr, get_ppa_metrics_for_apr, 
        get_sup_metrics_for_apr, get_dup_metrics_for_apr
    })
    
    model_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME")

    if model_deployment_name is not None:
        with agents_client:
            # Create individual metric agents
            pav_functions = FunctionTool(functions={get_pav_metrics_for_apr})
            
            pav_agent = agents_client.create_agent(
                model=model_deployment_name,
                name="PAV_Agent",
                instructions="""You are the PAV Agent, a Map and Geospatial expert who analyzes POI Availability (PAV) metrics only. 
                When given an APR number, use the get_pav_metrics_for_apr function with that APR number to fetch data, 
                analyze the patterns, and provide a concise summary of your findings. 
                Focus on significant patterns, outliers, and trends in the PAV data.
                Always mention how many rows of data you analyzed in your response.
                Do not analyze any other metric types.""",
                tools=pav_functions.definitions
            )

            ppa_functions = FunctionTool(functions={get_ppa_metrics_for_apr})
            
            ppa_agent = agents_client.create_agent(
                model=model_deployment_name,
                name="PPA_Agent", 
                instructions="""You are the PPA Agent, a Map and Geospatial expert who analyzes POI Positional Accuracy (PPA) metrics only.
                When given an APR number, use the get_ppa_metrics_for_apr function with that APR number to fetch data,
                analyze the patterns, and provide a concise summary of your findings.
                Focus on significant patterns, outliers, and trends in the PPA data.
                Always mention how many rows of data you analyzed in your response.
                Do not analyze any other metric types.""",
                tools=ppa_functions.definitions
            )

            sup_functions = FunctionTool(functions={get_sup_metrics_for_apr})
            
            sup_agent = agents_client.create_agent(
                model=model_deployment_name,
                name="SUP_Agent",
                instructions="""You are the SUP Agent, a Map and Geospatial expert who analyzes Superfluous (SUP) metrics only.
                When given an APR number, use the get_sup_metrics_for_apr function with that APR number to fetch data,
                analyze the patterns, and provide a concise summary of your findings.
                Focus on significant patterns, outliers, and trends in the SUP data.
                Always mention how many rows of data you analyzed in your response.
                Do not analyze any other metric types.""",
                tools=sup_functions.definitions
            )

            dup_functions = FunctionTool(functions={get_dup_metrics_for_apr})
            
            dup_agent = agents_client.create_agent(
                model=model_deployment_name,
                name="DUP_Agent",
                instructions="""You are the DUP Agent, a Map and Geospatial expert who analyzes Duplicate (DUP) metrics only.
                When given an APR number, use the get_dup_metrics_for_apr function with that APR number to fetch data,
                analyze the patterns, and provide a concise summary of your findings.
                Focus on significant patterns, outliers, and trends in the DUP data.
                Always mention how many rows of data you analyzed in your response.
                Do not analyze any other metric types.""",
                tools=dup_functions.definitions
            )

            # Create team leader with connected agent tools
            team_leader_functions = FunctionTool(functions=team_leader_function_set)
            
            # Create connected agent tool for PAV agent
            connected_pav_agent = ConnectedAgentTool(
                id=pav_agent.id, 
                name=pav_agent.name, 
                description="Analyzes POI Availability (PAV) metrics for a given APR number"
            )

            team_leader = agents_client.create_agent(
                model=model_deployment_name,
                name="APR Analysis Team Leader",
                instructions=f"""You are the APR Analysis Team Leader, an expert in Map and Geospatial analysis. 
                You lead a team of specialized metric analysis agents and coordinate comprehensive APR analysis.
                
                You have access to the following connected agent as a tool:
                - PAV_Agent: Use this to analyze POI Availability metrics for an APR

                You are conversational, helpful, and context-aware. For general questions, use your regular tools directly.
                
                When users request APR analysis (by providing an APR number like "121" or "APR-121"):
                1. Call PAV_Agent with the APR number (e.g., "121")
                2. Wait for the agent to complete its analysis  
                3. Provide a well-structured markdown report with the findings
                
                Format the final report professionally for easy copying and analysis.
                
                IMPORTANT: Call the PAV_Agent connected agent tool with the APR number as the input. 
                The tool expects just the APR number (e.g., "121") as input.""",
                tools=team_leader_functions.definitions + connected_pav_agent.definitions
            )

            print(f"\nAPR Analysis Team assembled with connected agents.")
            print("Team Leader connected to PAV agent only (for testing).")
            print("Type 'exit' or 'quit' to end the conversation.")

            # Create thread for conversation
            thread = agents_client.threads.create()
            print(f"Created thread for team leader, ID: {thread.id}")

            try:
                while True:
                    user_input = input("You: ")
                    if user_input.lower() in {"exit", "quit"}:
                        print("Ending conversation and deleting agents...")
                        break

                    # Send message to team leader
                    agents_client.messages.create(
                        thread_id=thread.id,
                        role="user", 
                        content=user_input
                    )

                    # Process with team leader (connected agents will be automatically coordinated)
                    print(f"\n🔄 Processing request with Team Leader...")
                    run = agents_client.runs.create_and_process(
                        thread_id=thread.id,
                        agent_id=team_leader.id
                    )
                    print(f"✅ Run completed - ID: {run.id}, Status: {run.status}")

                    # Get all messages to see the conversation flow
                    messages = list(agents_client.messages.list(thread_id=thread.id))
                    print(f"\n📋 Messages in thread ({len(messages)} total):")
                    
                    # Show last few messages
                    recent_messages = messages[:5] if len(messages) > 5 else messages  # Last 5 messages
                    for i, message in enumerate(reversed(recent_messages)):
                        role_emoji = "👤" if message.role == MessageRole.USER else "🤖"
                        content = message.content[0].text.value if message.content else "No content"
                        print(f"  {role_emoji} {message.role}: {content[:100]}...")
                        
                        # Try to identify the agent
                        if message.role == MessageRole.AGENT:
                            if hasattr(message, 'assistant_id'):
                                if message.assistant_id == pav_agent.id:
                                    print(f"      ^^ This was from PAV Agent (ID: {pav_agent.id})")
                                elif message.assistant_id == team_leader.id:
                                    print(f"      ^^ This was from Team Leader (ID: {team_leader.id})")

                    # Display the final response prominently
                    if messages:
                        final_message = messages[0]  # Most recent message
                        if final_message.role == MessageRole.AGENT:
                            print(f"\n📊 Final Response:")
                            print(f"{final_message.content[0].text.value}")
                            print(f"\n{'='*80}")

                    print(f"\n")

            finally:
                # Clean up agents
                print("Cleaning up agents...")
                agents_client.delete_agent(team_leader.id)
                agents_client.delete_agent(pav_agent.id)
                agents_client.delete_agent(ppa_agent.id) 
                agents_client.delete_agent(sup_agent.id)
                agents_client.delete_agent(dup_agent.id)
                print("All agents deleted.")

    else:
        print("Error: Please define the environment variable MODEL_DEPLOYMENT_NAME.")