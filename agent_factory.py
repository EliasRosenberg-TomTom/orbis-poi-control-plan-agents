from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FunctionTool
from agent_conf.AgentConf import AgentConf

class AgentFactory:
    def __init__(self, project_client, model_name):
        self.project_client = project_client
        self.model_name = model_name

    def create_agent(self, agent_conf: AgentConf):
        agent = self.project_client.agents.create_agent(
            model=self.model_name,
            name=agent_conf.agent_name,
            instructions=agent_conf.instructions,
            tools=agent_conf.tools
        )
        thread = self.project_client.agents.threads.create()
        print(f"Created agent '{agent_conf.agent_name}', ID: {agent.id}")
        print(f"Created thread for '{agent_conf.agent_name}', ID: {thread.id}")
        return agent, thread
