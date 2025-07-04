from langgraph.graph import StateGraph, END
from typing import Dict, Any, List
import json
from datetime import datetime

from place_search import PlacesDiscoveryService
from place_image import GooglePlacesService
from place_info import LangChainInfoService
from config import CATEGORIES

class TravelAssistantState:
    def __init__(self):
        self.location = ""
        self.raw_places = {}
        self.enriched_places = {}
        self.final_result = {}
        self.errors = []

class TravelAssistant:
    def __init__(self):
        self.discovery_service = PlacesDiscoveryService()
        self.google_service = GooglePlacesService()
        self.langchain_service = LangChainInfoService()
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph workflow"""
        workflow = StateGraph(dict)
        
        # Add nodes
        workflow.add_node("discover_places", self.discover_places_node)
        workflow.add_node("enrich_with_images", self.enrich_with_images_node)
        workflow.add_node("add_research", self.add_research_node)
        workflow.add_node("finalize_result", self.finalize_result_node)
        
        # Add edges
        workflow.set_entry_point("discover_places")
        workflow.add_edge("discover_places", "enrich_with_images")
        workflow.add_edge("enrich_with_images", "add_research")
        workflow.add_edge("add_research", "finalize_result")
        workflow.add_edge("finalize_result", END)
        
        return workflow.compile()
    
    def discover_places_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node 1: Discover places using SERP API and OpenAI"""
        try:
            raw_places = self.discovery_service.categorize_places(
                state["location"], 
                selected_categories=state.get("selected_categories")
            )
            state["raw_places"] = raw_places
            state["step"] = "discovery_complete"
        except Exception as e:
            state["errors"].append(f"Discovery error: {str(e)}")
        
        return state
    
    def enrich_with_images_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node 2: Enrich places with Google Places images and details"""
        try:
            enriched_places = self.google_service.enrich_places_with_images(
                state["raw_places"], 
                state["location"]
            )
            state["enriched_places"] = enriched_places
            state["step"] = "enrichment_complete"
        except Exception as e:
            state["errors"].append(f"Enrichment error: {str(e)}")
            # Use raw data if enrichment fails
            state["enriched_places"] = state["raw_places"]
        
        return state
    
    def add_research_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node 3: Add research using LangChain + Wikipedia + Tavily"""
        print("📚 Adding research insights...")
        
        try:
            final_data = self.langchain_service.enrich_with_research(
                state["enriched_places"],
                state["location"]
            )
            state["research_data"] = final_data
            state["step"] = "research_complete"
            print("✅ Research insights added")
        except Exception as e:
            state["errors"].append(f"Research error: {str(e)}")
            print(f"❌ Research failed: {e}")
            # Use enriched data without research if this fails
            state["research_data"] = {
                "location_overview": {"description": "Research unavailable"},
                "categories": state["enriched_places"]
            }
        
        return state
    
    def finalize_result_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node 4: Finalize and format the result"""
        # Transform data to the requested format
        formatted_result = {}
        
        for cat_key, cat_data in state["research_data"]["categories"].items():
            category_name = cat_key  # Use category key as the category name
            places_list = []
            
            for place in cat_data["places"]:
                # Extract the main image URL (first photo if available)
                place_image_url = ""
                if place.get("photos") and len(place["photos"]) > 0:
                    place_image_url = place["photos"][0]
                
                # Create the simplified place object
                place_obj = {
                    "tourist_place_name": place.get("name", ""),
                    "tourist_description": place.get("description", ""),
                    "place_image_url": place_image_url
                }
                places_list.append(place_obj)
            
            # Only include categories that have places
            if places_list:
                formatted_result[category_name] = places_list
        
        state["final_result"] = formatted_result
        state["step"] = "complete"
        
        return state
    
    def generate_travel_recommendations(self, location: str, selected_categories: List[str] = None) -> Dict[str, Any]:
        """Main method to generate travel recommendations"""
        # Initialize state
        initial_state = {
            "location": location,
            "selected_categories": selected_categories,
            "raw_places": {},
            "enriched_places": {},
            "research_data": {},
            "final_result": {},
            "errors": [],
            "step": "starting"
        }
        
        # Run the graph
        result = self.graph.invoke(initial_state)
        
        return result["final_result"]

def display_categories():
    """Display available categories for user selection"""
    print("\nAvailable Categories:")
    
    category_keys = list(CATEGORIES.keys())
    for i, (key, description) in enumerate(CATEGORIES.items(), 1):
        print(f"{i:2d}. {description}")
    
    return category_keys

def get_user_category_selection(category_keys):
    """Get user's category selection"""
    print(f"\nSelect categories (1-{len(category_keys)}):")
    print("   Enter numbers separated by commas (e.g., 1,3,5)")
    print("   Enter 'all' for all categories")
    print("   Press Enter for recommended categories (1,2,3)")
    
    while True:
        selection = input("\nYour selection: ").strip().lower()
        
        if not selection:
            # Default recommended categories
            return [category_keys[0], category_keys[1], category_keys[2]]  # natural, cultural, urban
        
        if selection == 'all':
            return category_keys
        
        try:
            # Parse comma-separated numbers
            selected_indices = [int(x.strip()) - 1 for x in selection.split(',')]
            
            # Validate indices
            if all(0 <= idx < len(category_keys) for idx in selected_indices):
                selected_categories = [category_keys[idx] for idx in selected_indices]
                return selected_categories
            else:
                print(f"Please enter numbers between 1 and {len(category_keys)}")
        
        except ValueError:
            print("Invalid input. Please enter numbers separated by commas, 'all', or press Enter for default.")

def main():
    """Demo function"""
    assistant = TravelAssistant()
    
    # Get location
    location = input("Enter a city or place to explore: ").strip()
    
    if not location:
        print("Please enter a valid location!")
        return
    
    # Display categories and get user selection
    category_keys = display_categories()
    selected_categories = get_user_category_selection(category_keys)
    
    # Generate recommendations for selected categories only
    recommendations = assistant.generate_travel_recommendations(location, selected_categories)
    
    # Save to file
    filename = f"travel_recommendations_{location.replace(' ', '_').lower()}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(recommendations, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to: {filename}")

if __name__ == "__main__":
    main()