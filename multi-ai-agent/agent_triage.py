import os
import json
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import Agent, AgentTool
from azure.identity import DefaultAzureCredential

# Clear the console
os.system('cls' if os.name=='nt' else 'clear')

# Load environment variables from .env file
load_dotenv()
project_endpoint = os.getenv("PROJECT_ENDPOINT")
model_deployment = os.getenv("MODEL_DEPLOYMENT_NAME")
credential = DefaultAzureCredential()

# Connect to the agents client
agents_client = AIProjectClient(endpoint=project_endpoint, credential=credential)

with agents_client:

    # Create an agent to prioritize support tickets
    prioritization_agent = agents_client.agents.create_agent(
        model=model_deployment,
        name="Ticket Prioritization Agent",
        instructions="You are an expert at prioritizing support tickets. Analyze the ticket content and assign a priority level (Critical, High, Medium, Low) based on urgency and impact.",
    )
    print(f"Created Prioritization Agent: {prioritization_agent.id}")

    # Create an agent to assign tickets to the appropriate team
    assignment_agent = agents_client.agents.create_agent(
        model=model_deployment,
        name="Ticket Assignment Agent",
        instructions="You are an expert at assigning support tickets to the right teams. Based on the ticket content, assign it to the appropriate team (Technical Support, Billing, Sales, General Support).",
    )
    print(f"Created Assignment Agent: {assignment_agent.id}")

    # Create an agent to estimate effort for a support ticket
    estimation_agent = agents_client.agents.create_agent(
        model=model_deployment,
        name="Effort Estimation Agent",
        instructions="You are an expert at estimating the effort required to resolve support tickets. Estimate the effort in hours (0.5, 1, 2, 4, 8, 16) based on the complexity and scope of the ticket.",
    )
    print(f"Created Estimation Agent: {estimation_agent.id}")

    # Define tools for connected agent communication
    def prioritize_ticket(ticket_content: str) -> str:
        """Tool to prioritize a support ticket"""
        pass

    def assign_ticket(ticket_content: str) -> str:
        """Tool to assign a support ticket"""
        pass

    def estimate_effort(ticket_content: str) -> str:
        """Tool to estimate effort for a support ticket"""
        pass

    # Create connected agent tools for the support agents
    tools = [
        AgentTool.from_function(
            function=prioritize_ticket,
            description="Prioritize a support ticket"
        ),
        AgentTool.from_function(
            function=assign_ticket,
            description="Assign a support ticket to the appropriate team"
        ),
        AgentTool.from_function(
            function=estimate_effort,
            description="Estimate the effort required to resolve a support ticket"
        ),
    ]

    # Create an agent to triage support ticket processing by using connected agents
    triage_agent = agents_client.agents.create_agent(
        model=model_deployment,
        name="Support Ticket Triage Agent",
        instructions="You are a support ticket triage coordinator. Your job is to analyze incoming support tickets and coordinate with specialized agents to prioritize, assign, and estimate effort for each ticket. Use the available tools to get prioritization, assignment, and effort estimation from specialist agents.",
        tools=tools,
    )
    print(f"Created Triage Agent: {triage_agent.id}")

    # Use the agents to triage a support issue
    sample_ticket = """
    Subject: Critical Database Connection Issue
    Description: Customer reports inability to connect to their production database. 
    The application is completely down and affecting 500+ users. Error message indicates 
    connection timeout after 30 seconds. Issue started 2 hours ago. Customer is a premium tier account.
    """

    print("\n--- Processing Support Ticket ---")
    print(f"Ticket: {sample_ticket}")

    # Create a thread and run triage
    thread = agents_client.agents.create_thread()
    agents_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content=f"Please triage this support ticket: {sample_ticket}",
    )

    run = agents_client.agents.create_run(
        thread_id=thread.id,
        assistant_id=triage_agent.id,
    )

    # Wait for completion
    while run.status == "queued" or run.status == "in_progress":
        run = agents_client.agents.get_run(thread_id=thread.id, run_id=run.id)

    # Get the response
    messages = agents_client.agents.list_messages(thread_id=thread.id)
    print("\n--- Triage Results ---")
    for message in messages.data:
        if message.role == "assistant":
            print(f"Triage Agent: {message.content[0].text}")

    # Clean up - delete agents
    agents_client.agents.delete_agent(prioritization_agent.id)
    agents_client.agents.delete_agent(assignment_agent.id)
    agents_client.agents.delete_agent(estimation_agent.id)
    agents_client.agents.delete_agent(triage_agent.id)
    agents_client.agents.delete_thread(thread.id)
    print("\n--- Cleanup Complete ---")

