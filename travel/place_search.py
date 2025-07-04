import requests
import json
from openai import OpenAI
from config import OPENAI_API_KEY, SERP_API_KEY, CATEGORIES

client = OpenAI(api_key=OPENAI_API_KEY)

class PlacesDiscoveryService:
    def __init__(self):
        self.serp_url = "https://serpapi.com/search"
        
    def search_places_with_serp(self, location, category):
        """Search for places using SERP API"""
        params = {
            "api_key": SERP_API_KEY,
            "engine": "google",
            "q": f"{category} in {location}",
            "location": location,
            "num": 10
        }
        
        try:
            # Add timeout to prevent hanging
            response = requests.get(self.serp_url, params=params, timeout=30)
            return response.json().get("organic_results", [])
        except requests.exceptions.Timeout:
            print(f"SERP API timeout for {category} in {location}")
            return []
        except Exception as e:
            print(f"SERP API error: {e}")
            return []
    
    def get_places_with_openai_web(self, location, category):
        """Use OpenAI web search to find places - using working technique from test.py"""
        try:
            response = client.responses.create(
                model="gpt-4.1",
                tools=[{"type": "web_search_preview"}],
                input=f"Find top 5 {category} places in {location}. For each place, provide: name, description, rating (if available), address. Format as JSON array with fields: name, description, rating, address. Make descriptions engaging for tourists."
            )
            
            content = response.output_text
            # Extract JSON from response
            start = content.find('[')
            end = content.rfind(']') + 1
            if start != -1 and end != 0:
                return json.loads(content[start:end])
            return []
            
        except Exception as e:
            print(f"OpenAI Web Search error: {e}")
            return []

    def categorize_places(self, location):
        """Find places for all relevant categories"""
        results = {}
        
        for cat_key, cat_desc in CATEGORIES.items():
            # Use both SERP and OpenAI for comprehensive results
            serp_results = self.search_places_with_serp(location, cat_desc.split('(')[0])
            openai_results = self.get_places_with_openai_web(location, cat_desc)
            
            places = []
            
            # Process SERP results
            for result in serp_results[:3]:
                places.append({
                    "name": result.get("title", ""),
                    "description": result.get("snippet", ""),
                    "url": result.get("link", ""),
                    "source": "serp"
                })
            
            # Process OpenAI results
            for result in openai_results[:3]:
                places.append({
                    "name": result.get("name", ""),
                    "description": result.get("description", ""),
                    "rating": result.get("rating", ""),
                    "address": result.get("address", ""),
                    "source": "openai"
                })
            
            if places:  # Only include categories with actual results
                results[cat_key] = {
                    "category": cat_desc,
                    "places": places
                }
        
        return results