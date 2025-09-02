from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder

from jira import JiraAPI

def get_jira_ticket_description(issue_id_or_key: str) -> str:
    jira = JiraAPI()
    return jira.get_ticket_description(issue_id_or_key)

project = AIProjectClient(
    credential=DefaultAzureCredential(),
    endpoint="https://controlplanvalidationagent.services.ai.azure.com/api/projects/firstProject"
)

agent = project.agents.get_agent("asst_mi6lhAjRECiS3fNR1htRsndi")

# Define tools as a list
tools = [
    {
        "name": "get_jira_ticket_description",
        "function": get_jira_ticket_description,
        "description": "Fetches the description of a Jira ticket by its ID or key."
    }
]

thread = project.agents.threads.create()
print(f"Created thread, ID: {thread.id}")

while True:
    user_input = input("You: ")
    if user_input.lower() in {"exit", "quit"}:
        print("Ending conversation.")
        break

    project.agents.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input
    )

    # Pass tools to the run (if required by SDK)
    run = project.agents.runs.create_and_process(
        thread_id=thread.id,
        agent_id=agent.id,
        tools=tools  # <-- Pass tools here if supported
    )

    if run.status == "failed":
        print(f"Run failed: {run.last_error}")
    else:
        messages = project.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
        for message in reversed(messages):
            if message.role == "assistant" and message.text_messages:
                print(f"Agent: {message.text_messages[-1].text.value}")
                break