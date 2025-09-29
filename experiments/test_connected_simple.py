import os
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FunctionTool, MessageRole, ConnectedAgentTool
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from agent_tools import get_pav_metrics_for_apr

load_dotenv()

project_endpoint = os.environ["AZURE_EXISTING_AIPROJECT_ENDPOINT"]
model_name = os.environ["MODEL_DEPLOYMENT_NAME"]

project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential(),
)

with project_client:
    agents_client = project_client.agents
    
    # Enable auto function calls
    agents_client.enable_auto_function_calls({get_pav_metrics_for_apr})
    
    model_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME")

    if model_deployment_name is not None:
        with agents_client:
            print("Creating PAV agent...")
            # Create PAV agent
            pav_functions = FunctionTool(functions={get_pav_metrics_for_apr})
            
            pav_agent = agents_client.create_agent(
                model=model_deployment_name,
                name="PAV_Agent",
                instructions="You are the PAV Agent. When given an APR number, use get_pav_metrics_for_apr to analyze the data.",
                tools=pav_functions.definitions
            )
            print(f"Created PAV agent: {pav_agent.id}")
            
            # Test PAV agent directly first
            print("\n=== Testing PAV agent directly ===")
            thread1 = agents_client.threads.create()
            
            agents_client.messages.create(
                thread_id=thread1.id,
                role="user", 
                content="Please analyze APR 121 using PAV metrics"
            )
            
            run1 = agents_client.runs.create_and_process(
                thread_id=thread1.id,
                agent_id=pav_agent.id
            )
            
            messages1 = list(agents_client.messages.list(thread_id=thread1.id))
            print(f"PAV Direct Response: {messages1[0].content[0].text.value}")
            
            # Now create connected agent
            print("\n=== Creating connected agent setup ===")
            connected_pav_agent = ConnectedAgentTool(
                id=pav_agent.id,
                name="PAV_Agent",
                description="Analyzes PAV metrics for APR"
            )
            print(f"Connected agent tool created")
            
            # Create simple team leader
            team_leader = agents_client.create_agent(
                model=model_deployment_name,
                name="Simple Leader",
                instructions="You have access to PAV_Agent tool. When user asks for APR analysis, call PAV_Agent with the APR number.",
                tools=connected_pav_agent.definitions
            )
            print(f"Created team leader: {team_leader.id}")
            
            # Test connected agent
            print("\n=== Testing connected agent ===")
            thread2 = agents_client.threads.create()
            
            agents_client.messages.create(
                thread_id=thread2.id,
                role="user", 
                content="Please analyze APR 121"
            )
            
            run2 = agents_client.runs.create_and_process(
                thread_id=thread2.id,
                agent_id=team_leader.id
            )
            
            messages2 = list(agents_client.messages.list(thread_id=thread2.id))
            print(f"Connected Agent Response: {messages2[0].content[0].text.value}")
            
            # Cleanup
            agents_client.delete_agent(team_leader.id)
            agents_client.delete_agent(pav_agent.id)
            print("Cleanup completed")
            
    else:
        print("Error: Please define MODEL_DEPLOYMENT_NAME")