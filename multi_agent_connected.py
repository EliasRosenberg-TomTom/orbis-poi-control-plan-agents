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
    model_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME")

    if model_deployment_name is not None:
        with agents_client:
            # Create individual metric agents
            pav_functions = FunctionTool(functions={get_pav_metrics_for_apr})
            pav_toolset = ToolSet()
            pav_toolset.add(pav_functions)
            
            pav_agent = agents_client.create_agent(
                model=model_deployment_name,
                name="PAV_Agent",
                instructions="""You are the PAV Agent, a Map and Geospatial expert who analyzes POI Availability (PAV) metrics only. 
                When given an APR number, use the get_pav_metrics_for_apr function with that APR number to fetch data, 
                analyze the patterns, and provide a concise summary of your findings. 
                Focus on significant patterns, outliers, and trends in the PAV data.
                Always mention how many rows of data you analyzed in your response.
                Do not analyze any other metric types.""",
                toolset=pav_toolset
            )

            ppa_functions = FunctionTool(functions={get_ppa_metrics_for_apr})
            ppa_toolset = ToolSet()
            ppa_toolset.add(ppa_functions)
            
            ppa_agent = agents_client.create_agent(
                model=model_deployment_name,
                name="PPA Agent", 
                instructions="""You are the PPA Agent, a Map and Geospatial expert who analyzes POI Positional Accuracy (PPA) metrics only.
                When given an APR number, use the get_ppa_metrics_for_apr function with that APR number to fetch data,
                analyze the patterns, and provide a concise summary of your findings.
                Focus on significant patterns, outliers, and trends in the PPA data.
                Always mention how many rows of data you analyzed in your response.
                Do not analyze any other metric types.""",
                toolset=ppa_toolset
            )

            sup_functions = FunctionTool(functions={get_sup_metrics_for_apr})
            sup_toolset = ToolSet()
            sup_toolset.add(sup_functions)
            
            sup_agent = agents_client.create_agent(
                model=model_deployment_name,
                name="SUP Agent",
                instructions="""You are the SUP Agent, a Map and Geospatial expert who analyzes Superfluous (SUP) metrics only.
                When given an APR number, use the get_sup_metrics_for_apr function with that APR number to fetch data,
                analyze the patterns, and provide a concise summary of your findings.
                Focus on significant patterns, outliers, and trends in the SUP data.
                Always mention how many rows of data you analyzed in your response.
                Do not analyze any other metric types.""",
                toolset=sup_toolset
            )

            dup_functions = FunctionTool(functions={get_dup_metrics_for_apr})
            dup_toolset = ToolSet()
            dup_toolset.add(dup_functions)
            
            dup_agent = agents_client.create_agent(
                model=model_deployment_name,
                name="DUP Agent",
                instructions="""You are the DUP Agent, a Map and Geospatial expert who analyzes Duplicate (DUP) metrics only.
                When given an APR number, use the get_dup_metrics_for_apr function with that APR number to fetch data,
                analyze the patterns, and provide a concise summary of your findings.
                Focus on significant patterns, outliers, and trends in the DUP data.
                Always mention how many rows of data you analyzed in your response.
                Do not analyze any other metric types.""",
                toolset=dup_toolset
            )

            # Create team leader with connected agent tools
            team_leader_functions = FunctionTool(functions=team_leader_function_set)
            
            # Create connected agent tools for each metric agent
            connected_pav_agent = ConnectedAgentTool(
                id=pav_agent.id, 
                name=pav_agent.name, 
                description="Analyzes POI Availability (PAV) metrics for a given APR number"
            )
            
            connected_ppa_agent = ConnectedAgentTool(
                id=ppa_agent.id,
                name=ppa_agent.name,
                description="Analyzes POI Positional Accuracy (PPA) metrics for a given APR number"
            )
            
            connected_sup_agent = ConnectedAgentTool(
                id=sup_agent.id, 
                name=sup_agent.name, 
                description="Analyzes Superfluous (SUP) metrics for a given APR number"
            )
            
            connected_dup_agent = ConnectedAgentTool(
                id=dup_agent.id, 
                name=dup_agent.name, 
                description="Analyzes Duplicate (DUP) metrics for a given APR number"
            )
            
            # Create toolset with function tools
            team_leader_toolset = ToolSet()
            team_leader_toolset.add(team_leader_functions)

            team_leader = agents_client.create_agent(
                model=model_deployment_name,
                name="APR Analysis Team Leader",
                instructions=f"""You are the APR Analysis Team Leader, an expert in Map and Geospatial analysis. 
                You lead a team of specialized metric analysis agents and coordinate comprehensive APR analysis.
                
                You have access to the following connected agents as tools:
                - PAV_Agent: Use this to analyze POI Availability metrics for an APR
                - PPA_Agent: Use this to analyze POI Positional Accuracy metrics for an APR  
                - SUP_Agent: Use this to analyze Superfluous metrics for an APR
                - DUP_Agent: Use this to analyze Duplicate metrics for an APR

                You are conversational, helpful, and context-aware. For general questions, use your regular tools directly.
                
                When users request APR analysis (by providing an APR number like "121" or "APR-121"):
                1. Call PAV_Agent with the APR number (e.g., "121")
                2. Call PPA_Agent with the APR number (e.g., "121")  
                3. Call SUP_Agent with the APR number (e.g., "121")
                4. Call DUP_Agent with the APR number (e.g., "121")
                5. Wait for all four agents to complete their analysis
                6. Combine their findings into a comprehensive, well-structured markdown report with clear sections:
                   - ## PAV Analysis (POI Availability)
                   - ## PPA Analysis (POI Positional Accuracy) 
                   - ## SUP Analysis (Superfluous)
                   - ## DUP Analysis (Duplicates)
                
                Format the final report professionally for easy copying and analysis. Do not just concatenate responses - 
                synthesize and organize the findings into a cohesive report.
                
                IMPORTANT: Call each connected agent tool one by one with the APR number as the input. 
                Each tool expects just the APR number (e.g., "121") as input.""",
                tools=connected_pav_agent.definitions
            )

            print(f"\nAPR Analysis Team assembled with connected agents.")
            print("Team Leader connected to PAV, PPA, SUP, and DUP agents.")
            print("Type 'exit' or 'quit' to end the conversation.")

            # Create thread for conversation
            thread = agents_client.threads.create()

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
                    run = agents_client.runs.create_and_process(
                        thread_id=thread.id,
                        agent_id=team_leader.id
                    )

                    # Get and display response
                    messages = agents_client.messages.list(thread_id=thread.id)
                    for message in messages:
                        if message.role == MessageRole.AGENT:
                            print(f"Team Leader: {message.content[0].text.value}")
                            break

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