from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FunctionTool
from agent_conf.AgentConf import AgentConf
from agent_tools import (get_jira_ticket_description, get_pull_request_body,
get_control_plan_metrics_from_pr_comment, get_jira_ticket_title, 
get_jira_ticket_release_notes, get_jira_ticket_attachments,
 get_jira_ticket_xlsx_attachment, get_apr_metrics)
import os
import json
import time

print("Starting create_agent.py")
print("loading env vars")
# Load environment variables
load_dotenv()

print("importing agent instructions")
instructions = AgentConf.load_agent_instructions("release-tag-llm-instructions.txt")

print("AZURE_EXISTING_AIPROJECT_ENDPOINT:", os.environ.get("AZURE_EXISTING_AIPROJECT_ENDPOINT"))
print("MODEL_DEPLOYMENT_NAME:", os.environ.get("MODEL_DEPLOYMENT_NAME"))

# Define user functions
user_functions = {get_jira_ticket_description, get_pull_request_body, get_control_plan_metrics_from_pr_comment,
                   get_jira_ticket_title, get_jira_ticket_release_notes, get_jira_ticket_xlsx_attachment, 
                   get_jira_ticket_attachments, get_apr_metrics}

# Map tool names to Python functions, used for terminal chat only. 
tool_function_map = {
    "get_jira_ticket_description": get_jira_ticket_description,
    "get_pull_request_body": get_pull_request_body,
    "get_control_plan_metrics_from_pr_comment": get_control_plan_metrics_from_pr_comment,
    "get_jira_ticket_title": get_jira_ticket_title,
    "get_jira_ticket_release_notes": get_jira_ticket_release_notes,
    "get_jira_ticket_attachments": get_jira_ticket_attachments,
    "get_jira_ticket_xlsx_attachment": get_jira_ticket_xlsx_attachment,
    "get_apr_metrics": get_apr_metrics,
}


project_endpoint = os.environ["AZURE_EXISTING_AIPROJECT_ENDPOINT"]
model_name = os.environ["MODEL_DEPLOYMENT_NAME"]

project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential()
)

functions = FunctionTool(functions=user_functions)

with project_client:
    agent = project_client.agents.create_agent(
        model=model_name,
        name="rc-nightly-test-agent",
        instructions=instructions,
        tools=functions.definitions,
    )
    print(f"Created agent, ID: {agent.id}")

    thread = project_client.agents.threads.create()
    print(f"Created thread, ID: {thread.id}")

    try:
        while True:
            user_input = input("You: ")
            if user_input.lower() in {"exit", "quit"}:
                print("Ending conversation.")
                break

            project_client.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_input,
            )

            run = project_client.agents.runs.create(thread_id=thread.id, agent_id=agent.id)

            # Poll the run status until it is completed or requires action
            while run.status in ["queued", "in_progress", "requires_action"]:
                time.sleep(1)
                run = project_client.agents.runs.get(thread_id=thread.id, run_id=run.id)

                if run.status == "requires_action":
                    tool_calls = run.required_action.submit_tool_outputs.tool_calls
                    tool_outputs = []
                    for tool_call in tool_calls:
                        func_name = tool_call.function.name
                        args = tool_call.function.arguments
                        if isinstance(args, str):
                            args = json.loads(args)
                        func = tool_function_map.get(func_name)
                        if func:
                            try:
                                output = func(**args)
                            except Exception as e:
                                output = f"Error running tool '{func_name}': {e}"
                        else:
                            output = f"Unknown tool: {func_name}"
                        tool_outputs.append({"tool_call_id": tool_call.id, "output": output})
                    project_client.agents.runs.submit_tool_outputs(
                        thread_id=thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )

            messages = list(project_client.agents.messages.list(thread_id=thread.id))
            for message in messages:
                if message.role == "assistant" and message.text_messages:
                    print(f"Agent: {message.text_messages[-1].text.value}")
                    break
    finally:
        # Delete the agent after use
        project_client.agents.delete_agent(agent.id)
        print("Deleted agent")