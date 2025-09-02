import os
import time
import json
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FunctionTool
from jira.JiraAPI import JiraAPI
from github.GithubAPI import GithubAPI
print("Starting create_agent.py")
print("loading env vars")
# Load environment variables
load_dotenv()

print("AZURE_EXISTING_AIPROJECT_ENDPOINT:", os.environ.get("AZURE_EXISTING_AIPROJECT_ENDPOINT"))
print("MODEL_DEPLOYMENT_NAME:", os.environ.get("MODEL_DEPLOYMENT_NAME"))

def get_jira_ticket_description(issue_id_or_key: str) -> str:
    """
    Fetches the description of a Jira ticket by its ID or key.

    :param issue_id_or_key: The Jira issue ID or key (e.g., 'MPOI-6652').
    :return: The ticket description as a string.
    """
    jira = JiraAPI()
    return jira.get_ticket_description(issue_id_or_key)

def get_pull_request_body(pr_id: str) -> str:
    """
    Fetches the body of a pull request by its pr issue number.

    :param pr_id: The pull request ID (e.g., '123').
    :return: The pull request body as a string.
    """
    gh = GithubAPI()
    return gh.get_pull_request_body(pr_id)

# Define user functions
user_functions = {get_jira_ticket_description}

# Retrieve required environment variables
project_endpoint = os.environ["AZURE_EXISTING_AIPROJECT_ENDPOINT"]
model_name = os.environ["MODEL_DEPLOYMENT_NAME"]

# Initialize the AIProjectClient
project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential()
)

# Initialize the FunctionTool with user-defined functions
functions = FunctionTool(functions=user_functions)

with project_client:
    # Create an agent with custom functions
    agent = project_client.agents.create_agent(
        model=model_name,
        name="jira-agent",
        instructions="You are a helpful agent that can fetch Jira ticket descriptions.",
        tools=functions.definitions,
    )
    print(f"Created agent, ID: {agent.id}")

    # Create a thread for communication
    thread = project_client.agents.threads.create()
    print(f"Created thread, ID: {thread.id}")

    # Interactive conversation loop
    try:
        while True:
            user_input = input("You: ")
            if user_input.lower() in {"exit", "quit"}:
                print("Ending conversation.")
                break

            # Send a message to the thread
            message = project_client.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_input,
            )

            # Create and process a run for the agent to handle the message
            run = project_client.agents.runs.create(thread_id=thread.id, agent_id=agent.id)

            # Poll the run status until it is completed or requires action
            while run.status in ["queued", "in_progress", "requires_action"]:
                time.sleep(1)
                run = project_client.agents.runs.get(thread_id=thread.id, run_id=run.id)

                if run.status == "requires_action":
                    tool_calls = run.required_action.submit_tool_outputs.tool_calls
                    tool_outputs = []
                    for tool_call in tool_calls:
                        if tool_call.function.name == "get_jira_ticket_description":
                            # Extract argument from tool_call
                            args = tool_call.function.arguments
                            # Azure SDK may pass arguments as a JSON string
                            if isinstance(args, str):
                                args = json.loads(args)
                            issue_id_or_key = args.get("issue_id_or_key")
                            output = get_jira_ticket_description(issue_id_or_key)
                            tool_outputs.append({"tool_call_id": tool_call.id, "output": output})
                    project_client.agents.runs.submit_tool_outputs(
                        thread_id=thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )

            # Fetch and print the latest assistant message
            messages = list(project_client.agents.messages.list(thread_id=thread.id))
            for message in messages:
                if message.role == "assistant" and message.text_messages:
                    print(f"Agent: {message.text_messages[-1].text.value}")
                    break

    finally:
        # Delete the agent after use
        project_client.agents.delete_agent(agent.id)
        print("Deleted agent")