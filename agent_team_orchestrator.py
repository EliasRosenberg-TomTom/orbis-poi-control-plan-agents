

import os
from typing import Set

from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ToolSet, FunctionTool
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from utils.agent_team import AgentTeam, _create_task
from utils.agent_trace_configurator import AgentTraceConfigurator
from agent_tools import (get_jira_ticket_description, get_pull_request_body,
get_control_plan_metrics_from_pr_comment, get_jira_ticket_title, 
get_jira_ticket_release_notes, get_jira_ticket_attachments,
 get_jira_ticket_xlsx_attachment, get_apr_metrics, 
 get_PRs_from_apr, get_pull_request_title)

load_dotenv()

project_endpoint = os.environ["AZURE_EXISTING_AIPROJECT_ENDPOINT"]
model_name = os.environ["MODEL_DEPLOYMENT_NAME"]

project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential(),
)

orchestrator_function_set: Set = {_create_task, get_jira_ticket_description, get_pull_request_body, get_pull_request_title,  get_control_plan_metrics_from_pr_comment, get_jira_ticket_title, get_jira_ticket_release_notes, get_jira_ticket_xlsx_attachment, get_jira_ticket_attachments, get_apr_metrics, get_PRs_from_apr} #not sure if I need anything here just yet

with project_client:
    agents_client = project_client.agents

    agents_client.enable_auto_function_calls(
        {
            _create_task,
            get_jira_ticket_description,
            get_pull_request_body, 
            get_pull_request_title,  
            get_control_plan_metrics_from_pr_comment,
            get_jira_ticket_title, 
            get_jira_ticket_release_notes,
            get_jira_ticket_xlsx_attachment, 
            get_jira_ticket_attachments, 
            get_apr_metrics, 
            get_PRs_from_apr
        }
    )

    model_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME")

    if model_deployment_name is not None:
        with agents_client:

            orchestrator_functions = FunctionTool(functions=orchestrator_function_set)
            orchestrator_toolset = ToolSet()
            orchestrator_toolset.add(orchestrator_functions)

            agent_team = AgentTeam("apr analysis team", agents_client=agents_client)

            agent_team.set_team_leader(
                model=model_deployment_name,
                name="TeamLeader",
                instructions="""
                You are the TeamLeader agent for the APR analysis team. Your team consists of:
                - PAV agent: analyzes only PAV metrics
                - PPA agent: analyzes only PPA metrics
                - SUP agent: analyzes only SUP metrics
                - DUP agent: analyzes only DUP metrics

                You are expected to be conversational, helpful, and context-aware. Respond to general questions, comments, or requests in a natural, friendly way. Use your available tools to answer user questions directly when possible.

                Use your own semantic understanding and reasoning to determine when the user is requesting APR analysis (such as by providing an APR number, asking for APR metric analysis, or making it clear they want a full APR report). Do not rely on hardcoded string parsing or keyword matching; instead, interpret the user's intent naturally as a capable AI agent.

                When you determine that APR analysis is requested, create tasks for all four agents using the _create_task function, passing the correct metric type for each agent. For example:
                _create_task('apr analysis team', 'PAV agent', 'Analyze APR number 121 for PAV metrics', 'TeamLeader')
                _create_task('apr analysis team', 'PPA agent', 'Analyze APR number 121 for PPA metrics', 'TeamLeader')
                _create_task('apr analysis team', 'SUP agent', 'Analyze APR number 121 for SUP metrics', 'TeamLeader')
                _create_task('apr analysis team', 'DUP agent', 'Analyze APR number 121 for DUP metrics', 'TeamLeader')

                Wait for all agents to return their summaries. Then, create a single task for yourself to combine their summaries into a markdown report and return it to the user. Do not analyze any metric yourself except for combining the results. Make sure each agent only analyzes its own metric type, and please structure your final analysis as markdown so I can copy and analyze it easily.

                If the user does not request APR analysis, continue the conversation normally, answer questions, and do not create any analysis tasks. Use your tools and capabilities to help the user as a general chatbot when appropriate.
                """,
                toolset=orchestrator_toolset,
            )

            # Create a unique ToolSet for each agent
            pav_functions = FunctionTool(functions={get_control_plan_metrics_from_pr_comment})
            pav_toolset = ToolSet()
            pav_toolset.add(pav_functions)

            ppa_functions = FunctionTool(functions={get_control_plan_metrics_from_pr_comment})
            ppa_toolset = ToolSet()
            ppa_toolset.add(ppa_functions)

            sup_functions = FunctionTool(functions={get_control_plan_metrics_from_pr_comment})
            sup_toolset = ToolSet()
            sup_toolset.add(sup_functions)

            dup_functions = FunctionTool(functions={get_control_plan_metrics_from_pr_comment})
            dup_toolset = ToolSet()
            dup_toolset.add(dup_functions)

            agent_team.add_agent(
                model=model_deployment_name,
                name="PAV agent",
                instructions="You are the PAV agent. Only analyze PAV metrics. When assigned a task, use the get_apr_metrics function to get PAV metrics for the given APR number, analyze for patterns, and report your findings back to the TeamLeader. Do not analyze any other metric type.",
                toolset=pav_toolset,
                can_delegate=False,
            )

            agent_team.add_agent(
                model=model_deployment_name,
                name="PPA agent",
                instructions="You are the PPA agent. Only analyze PPA metrics. When assigned a task, use the get_apr_metrics function to get PPA metrics for the given APR number, analyze for patterns, and report your findings back to the TeamLeader. Do not analyze any other metric type.",
                toolset=ppa_toolset,
                can_delegate=False,
            )

            agent_team.add_agent(
                model=model_deployment_name,
                name="SUP agent",
                instructions="You are the SUP agent. Only analyze SUP metrics. When assigned a task, use the get_apr_metrics function to get SUP metrics for the given APR number, analyze for patterns, and report your findings back to the TeamLeader. Do not analyze any other metric type.",
                toolset=sup_toolset,
                can_delegate=False,
            )

            agent_team.add_agent(
                model=model_deployment_name,
                name="DUP agent",
                instructions="You are the DUP agent. Only analyze DUP metrics. When assigned a task, use the get_apr_metrics function to get DUP metrics for the given APR number, analyze for patterns, and report your findings back to the TeamLeader. Do not analyze any other metric type.",
                toolset=dup_toolset,
                can_delegate=False,
            )

            agent_team.assemble_team()

            print(f"\nTeam '{agent_team.team_name}' assembled. You are now chatting with the TeamLeader agent.")
            print("Type 'exit' or 'quit' to end the conversation.")

            while True:
                user_input = input("You: ")
                if user_input.lower() in {"exit", "quit"}:
                    print("Ending conversation and deleting agents...")
                    break
                agent_team.process_request(request=user_input)

            agent_team.dismantle_team()
    else:
        print("Error: Please define the environment variable MODEL_DEPLOYMENT_NAME.")