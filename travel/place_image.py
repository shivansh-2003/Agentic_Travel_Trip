import requests
import json
from config import GOOGLE_API_KEY

class GooglePlacesService:
    def __init__(self):
        self.api_key = GOOGLE_API_KEY
        self.places_url = "https://maps.googleapis.com/maps/api/place"
        
    def search_place(self, place_name, location):
        """Search for a place using Google Places API"""
        url = f"{self.places_url}/textsearch/json"
        params = {
            "query": f"{place_name} {location}",
            "key": self.api_key,
            "fields": "place_id,name,formatted_address,rating,photos,geometry"
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            return data.get("results", [])
        except Exception as e:
            print(f"Google Places search error: {e}")
            return []
    
    def get_place_details(self, place_id):
        """Get detailed information about a place"""
        url = f"{self.places_url}/details/json"
        params = {
            "place_id": place_id,
            "fields": "name,formatted_address,rating,photos,opening_hours,website,formatted_phone_number",
            "key": self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            return response.json().get("result", {})
        except Exception as e:
            print(f"Google Places details error: {e}")
            return {}
    
    def get_photo_url(self, photo_reference, max_width=400):
        """Get photo URL from photo reference"""
        return f"{self.places_url}/photo?maxwidth={max_width}&photoreference={photo_reference}&key={self.api_key}"
    
    def enrich_places_with_images(self, places_data, location):
        """Add images and additional details to places"""
        enriched_data = {}
        
        for category, cat_data in places_data.items():
            enriched_places = []
            
            for place in cat_data["places"]:
                # Search for the place on Google
                search_results = self.search_place(place["name"], location)
                
                if search_results:
                    google_place = search_results[0]
                    place_id = google_place.get("place_id")
                    
                    # Get detailed information
                    details = self.get_place_details(place_id) if place_id else {}
                    
                    # Extract photos
                    photos = google_place.get("photos", [])
                    photo_urls = []
                    for photo in photos[:3]:  # Get up to 3 photos
                        photo_ref = photo.get("photo_reference")
                        if photo_ref:
                            photo_urls.append(self.get_photo_url(photo_ref))
                    
                    # Enrich place data
                    enriched_place = {
                        **place,
                        "google_rating": google_place.get("rating"),
                        "address": google_place.get("formatted_address", place.get("address", "")),
                        "photos": photo_urls,
                        "website": details.get("website"),
                        "phone": details.get("formatted_phone_number"),
                        "opening_hours": details.get("opening_hours", {}).get("weekday_text", []),
                        "coordinates": {
                            "lat": google_place.get("geometry", {}).get("location", {}).get("lat"),
                            "lng": google_place.get("geometry", {}).get("location", {}).get("lng")
                        }
                    }
                    enriched_places.append(enriched_place)
                else:
                    # Keep original place data if Google search fails
                    enriched_places.append(place)
            
            enriched_data[category] = {
                **cat_data,
                "places": enriched_places
            }
        
        return enriched_data