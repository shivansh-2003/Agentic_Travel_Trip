from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY, TAVILY_API_KEY
import json

class LangChainInfoService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=OPENAI_API_KEY,
            temperature=0.3
        )
        
        # Initialize Wikipedia tool
        self.wikipedia = WikipediaQueryRun(
            api_wrapper=WikipediaAPIWrapper(
                wiki_client=None,
                top_k_results=2,
                doc_content_chars_max=2000
            )
        )
        
        # Initialize Tavily search tool
        self.tavily = TavilySearchResults(
            api_key=TAVILY_API_KEY,
            max_results=3
        )
        
        # Create agent with tools
        self.tools = [self.wikipedia, self.tavily]
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=False,
            return_intermediate_steps=True
        )
    
    def get_location_info(self, location):
        """Get comprehensive information about a location"""
        query = f"Tell me about {location} - its history, culture, geography, and what makes it special for tourists"
        
        try:
            result = self.agent.invoke({"input": query})
            return {
                "location": location,
                "description": result["output"],
                "sources": "Wikipedia and Tavily Search"
            }
        except Exception as e:
            print(f"LangChain info error: {e}")
            return {
                "location": location,
                "description": f"Unable to fetch detailed information about {location}",
                "sources": "Error"
            }
    
    def get_place_insights(self, place_name, location):
        """Get detailed insights about a specific place"""
        query = f"Provide interesting facts and travel tips about {place_name} in {location}"
        
        try:
            result = self.agent.invoke({"input": query})
            return {
                "place": place_name,
                "insights": result["output"],
                "research_sources": "Wikipedia and Tavily"
            }
        except Exception as e:
            print(f"Place insights error: {e}")
            return {
                "place": place_name,
                "insights": f"Unable to fetch insights about {place_name}",
                "research_sources": "Error"
            }
    
    def enrich_with_research(self, enriched_places_data, location):
        """Add research-based information to places data"""
        # Get general location information
        location_info = self.get_location_info(location)
        
        # Add insights to top places in each category
        for category, cat_data in enriched_places_data.items():
            if cat_data["places"]:
                # Get insights for the top-rated place in each category
                top_place = cat_data["places"][0]
                insights = self.get_place_insights(top_place["name"], location)
                top_place["ai_insights"] = insights["insights"]
        
        return {
            "location_overview": location_info,
            "categories": enriched_places_data
        }