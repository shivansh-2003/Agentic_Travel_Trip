import json
import re
from openai import OpenAI
from config import OPENAI_API_KEY, CATEGORIES

client = OpenAI(api_key=OPENAI_API_KEY)

class PlacesDiscoveryService:
    def __init__(self):
        pass
    
    def filter_irrelevant_results(self, places, location):
        """Filter out irrelevant search results and generic titles"""
        filtered_places = []
        
        # Patterns to identify and remove irrelevant results
        irrelevant_patterns = [
            r'^THE \d+ BEST',  # "THE 10 BEST..."
            r'^Top \d+',       # "Top 10..."
            r'^Best \d+',      # "Best 5..."
            r'^(\d+) Best',    # "10 Best..."
            r'UPDATED \d{4}',  # "UPDATED 2025"
            r'- Students',     # Educational generic results
            r'near me',        # "places near me"
            r'^\d+\.',         # Starting with numbers like "1. Place"
            r'Manufacturers',  # Equipment manufacturers
            r'Supplier',       # Equipment suppliers
            r'Tours in',       # Generic tour titles
            r'Activities in',  # Generic activity titles
            r'Things to Do',   # Generic things to do
        ]
        
        # Generic location patterns to avoid
        location_generic = [
            f"{location} -",
            f"in {location}",
            f"{location} Guide",
            f"{location} Tourism",
            f"Culture & Heritage - India",
            f"Explore {location}",
            f"Visiting {location}",
        ]
        
        for place in places:
            name = place.get('name', '').strip()
            description = place.get('description', '').strip()
            
            # Skip empty names
            if not name or len(name) < 3:
                continue
                
            # Check for irrelevant patterns
            is_irrelevant = False
            for pattern in irrelevant_patterns:
                if re.search(pattern, name, re.IGNORECASE):
                    is_irrelevant = True
                    break
            
            # Check for generic location results
            for generic in location_generic:
                if generic.lower() in name.lower():
                    is_irrelevant = True
                    break
            
            # Skip if description looks like a search result snippet
            if '...' in name or name.endswith('...'):
                is_irrelevant = True
            
            # Skip if name is too long (likely an article title)
            if len(name) > 80:
                is_irrelevant = True
                
            if not is_irrelevant:
                filtered_places.append(place)
        
        return filtered_places

    def get_places_with_openai_web(self, location, category):
        """Use OpenAI web search with better prompting for actual places"""
        try:
            # Create a more specific prompt that asks for actual place names
            prompt = f"""Find actual tourist places and attractions in {location} that fall under the category: {category}.

IMPORTANT REQUIREMENTS:
- Return ONLY real, specific place names (not article titles, listicles, or generic descriptions)
- Focus on actual locations tourists can visit
- Provide the official name of each place
- Include a brief, factual description of what the place is
- If a place has an address, include it
- Only include places that actually exist and are open to visitors

Return results as a JSON array with this exact format:
[
  {{
    "name": "Exact place name",
    "description": "Brief factual description of what this place is",
    "address": "Address if known"
  }}
]

Category: {category}
Location: {location}

Find between 1-8 actual places that tourists can visit. Quality over quantity."""

            response = client.responses.create(
                model="gpt-4.1",
                tools=[{"type": "web_search_preview"}],
                input=prompt
            )
            
            content = response.output_text
            # Extract JSON from response
            start = content.find('[')
            end = content.rfind(']') + 1
            if start != -1 and end != 0:
                places = json.loads(content[start:end])
                # Filter the results
                return self.filter_irrelevant_results(places, location)
            return []
            
        except Exception as e:
            return []

    def categorize_places(self, location, selected_categories=None):
        """Find actual places for selected categories - web search only"""
        results = {}
        
        # Use selected categories or all categories if none specified
        if selected_categories:
            categories_to_search = {key: CATEGORIES[key] for key in selected_categories if key in CATEGORIES}
        else:
            categories_to_search = CATEGORIES
        
        for cat_key, cat_desc in categories_to_search.items():
            category_name = cat_desc.split('(')[0].strip()
            
            # Use OpenAI Web Search only
            web_results = self.get_places_with_openai_web(location, category_name)
            
            # Process and filter results
            final_places = []
            for result in web_results:
                place = {
                    "name": result.get("name", ""),
                    "description": result.get("description", ""),
                    "rating": result.get("rating", ""),
                    "address": result.get("address", ""),
                    "source": "openai_web"
                }
                
                # Quality filter
                name = place.get('name', '').strip()
                if name and len(name) > 2 and len(name) < 80:
                    final_places.append(place)
            
            # Only include categories that have actual places
            if final_places:
                results[cat_key] = {
                    "category": cat_desc,
                    "places": final_places
                }
        
        return results