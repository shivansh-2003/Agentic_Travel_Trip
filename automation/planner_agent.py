import json
import os
from typing import Dict, Optional
from langchain.agents import initialize_agent, AgentType
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

class FlightSearchQuery:
    def __init__(self, departure_city: str, destination_city: str, departure_date: str, return_date: str):
        self.departure_city = departure_city
        self.destination_city = destination_city
        self.departure_date = departure_date
        self.return_date = return_date

class FlightPlannerTool(BaseTool):
    name = "flight_search_planner"
    description = "Generates step-by-step instructions for searching flights on Google Flights"
    
    def _run(self, query: str) -> str:
        try:
            flight_query = self._parse_query(query)
            steps = self._generate_search_steps(flight_query)
            return json.dumps(steps, indent=2)
        except Exception as e:
            return f"Error generating flight search plan: {str(e)}"
    
    async def _arun(self, query: str) -> str:
        return self._run(query)
    
    def _parse_query(self, query: str) -> FlightSearchQuery:
        llm = ChatOpenAI(temperature=0, model_name="gpt-4o")
        extraction_prompt = f"""
        Extract flight search parameters from this query: "{query}"
        the out of LLm response should be this 
        Return a series of steps to search for flights on Google Flights.
        Go to Google Flights and search for:
        - Click on the departure city input field
        - Type London as the departure city and press enter
        - Click on the destination city input field
        - Type Paris as the destination city and press enter
        - Click on the departure date input field
        - Type 30-06-2025 as the departure date and press enter
        - Click on the return date input field
        - Type 07-07-2025 as the return date and press enter
        - Click search for flights
        - Sort by price
        - Extract the following information and provide them as the final result in JSON format:
          * Flight price
          * Airline name
          * Departure time
          * Arrival time
          * Number of stops
          * Total travel time
          * Flight number (if available)
          * Booking url
        """
        try:
            result = llm(extraction_prompt)
            result = result.strip()
            if result.startswith('```json'):
                result = result.replace('```json', '').replace('```', '')
            parsed_data = json.loads(result)
            return FlightSearchQuery(
                departure_city=parsed_data.get("departure_city", "NOT_SPECIFIED"),
                destination_city=parsed_data.get("destination_city", "NOT_SPECIFIED"),
                departure_date=parsed_data.get("departure_date", "NOT_SPECIFIED"),
                return_date=parsed_data.get("return_date", "NOT_SPECIFIED")
            )
        except Exception as e:
            print(f"Warning: Failed to parse query '{query}'. Error: {str(e)}")
            return FlightSearchQuery("NOT_SPECIFIED", "NOT_SPECIFIED", "NOT_SPECIFIED", "NOT_SPECIFIED")
    
    def _generate_search_steps(self, flight_query: FlightSearchQuery) -> Dict:
        return {
            "automation_steps": [
                {"step": 1, "action": "navigate_to_google_flights", "instruction": "Go to Google Flights (https://flights.google.com)"},
                {"step": 2, "action": "click_departure_city_field", "instruction": "Click on the departure city input field"},
                {"step": 3, "action": "enter_departure_city", "instruction": f"Type {flight_query.departure_city} and press enter"},
                {"step": 4, "action": "click_destination_city_field", "instruction": "Click on the destination city input field"},
                {"step": 5, "action": "enter_destination_city", "instruction": f"Type {flight_query.destination_city} and press enter"},
                {"step": 6, "action": "click_departure_date_field", "instruction": "Click on the departure date input field"},
                {"step": 7, "action": "enter_departure_date", "instruction": f"Type {flight_query.departure_date} and press enter"},
                {"step": 8, "action": "click_return_date_field", "instruction": "Click on the return date input field"},
                {"step": 9, "action": "enter_return_date", "instruction": f"Type {flight_query.return_date} and press enter"},
                {"step": 10, "action": "click_search_button", "instruction": "Click search for flights"},
                {"step": 11, "action": "sort_by_price", "instruction": "Sort by price"}
            ],
            "final_result": {
                "instructions": "Extract the following information in JSON format:",
                "fields": ["Flight price", "Airline name", "Departure time", "Arrival time", "Number of stops", "Total travel time", "Flight number (if available)","Booking url"]
            }
        }

    def generate_automation_steps(self, user_query: str) -> Dict:
        if not user_query.strip():
            return {"error": "User query cannot be empty"}
        try:
            result = self.agent.run(f"Generate flight search steps for: {user_query}")
            return json.loads(result)
        except Exception as e:
            return {"error": f"Failed to generate automation steps: {str(e)}"}
    
    def generate_steps_text_format(self, query: str) -> str:
        """Generate steps in the human-readable text format"""
        try:
            flight_query = self._parse_query(query)
            
            steps_text = f"""Go to Google Flights and search for:
        - Click on the departure city input field
        - Type {flight_query.departure_city} as the departure city and press enter
        - Click on the destination city input field
        - Type {flight_query.destination_city} as the destination city and press enter
        - Click on the departure date input field
        - Type {flight_query.departure_date} as the departure date and press enter
        - Click on the return date input field
        - Type {flight_query.return_date} as the return date and press enter
        - Click search for flights
        - Sort by price
        - Extract the following information and provide them as the final result in JSON format:
          * Flight price
          * Airline name
          * Departure time
          * Arrival time
          * Number of stops
          * Total travel time
          * Flight number (if available)
          * Booking url"""
            
            return steps_text
        except Exception as e:
            return f"Error generating steps: {str(e)}"

# Usage Example
def main():
    """Simple demonstration of automation step generation"""
    try:
        # Initialize the agent
        agent = FlightPlannerTool()
        
        # Get user query
        user_query = input("Enter your flight search query: ")
        
        print("\n🔄 Generating automation steps...")
        
        # Generate steps in text format (the format you requested)
        print("✅ Generated Steps (Text Format):")
        steps_text = agent.generate_steps_text_format(user_query)
        print(steps_text)
        
        print("\n" + "="*50 + "\n")
        
        # Generate steps in JSON format
        print("✅ Generated Steps (JSON Format):")
        steps_json = agent._generate_search_steps(agent._parse_query(user_query))
        print(json.dumps(steps_json, indent=2))
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("💡 Make sure to set your OPENAI_API_KEY environment variable")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    main()