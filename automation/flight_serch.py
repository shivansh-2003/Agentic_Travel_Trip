from browser_use.llm import ChatOpenAI
from browser_use import Agent, BrowserSession
from planner_agent import FlightStepGenerator
from dotenv import load_dotenv
import asyncio
import json

load_dotenv()

browser_session = BrowserSession(
    headless=True,
    viewport={'width': 964, 'height': 647},
    user_data_dir='~/.config/browseruse/profiles/default',
)
llm = ChatOpenAI(model="gpt-4o")

async def main():
    """Function to execute the Google Flights search task."""
    
    # Get user query for flight search
    user_query = input("Enter your flight search query: ")
    
    # Generate task details using FlightStepGenerator
    generator = FlightStepGenerator()
    step_details = generator.generate_steps(user_query)
    
    if "error" in step_details:
        print(f"Error generating steps: {step_details['error']}")
        return
    
    # Convert automation steps to task instructions
    task_instructions = []
    task_instructions.append("Go to Google Flights and search for:")
    
    for step in step_details.get("automation_steps", []):
        task_instructions.append(f"- {step['instruction']}")
    
    # Add extraction instructions
    extract_fields = step_details.get("extract_fields", [])
    if extract_fields:
        task_instructions.append("- Extract the following information and provide them as the final result in JSON format:")
        for field in extract_fields:
            task_instructions.append(f"  * {field.replace('_', ' ').title()}")
    
    # Create the final task string
    TASK = "\n".join(task_instructions)
    
    print(f"\nGenerated Task:\n{TASK}\n")
    print(f"Extracted Flight Details: {json.dumps(step_details.get('extracted_details', {}), indent=2)}\n")
    
    # Execute the task with browser automation
    agent = Agent(
        task=TASK,
        llm=llm,
        browser_session=browser_session,
        validate_output=True,
        enable_memory=True,
        max_actions_per_step=1
    )
    
    result = await agent.run()
    print("Flight Search Results:")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())