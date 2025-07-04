import requests

def search_airport_id(query, language_code="en-US", country_code="US", api_key="00c4aad806msh8e00931585a4552p1cba4fjsn25893b3ff1c5"):
    """
    Search for airport ID using Google Flights API
    
    Args:
        query (str): The search term to find an airport (place name, city, or airport code)
        language_code (str, optional): Language code for response. Defaults to "en-US"
        country_code (str, optional): Country code for filtering results. Defaults to "US"
        api_key (str): RapidAPI key for authentication
    
    Returns:
        str or None: Airport ID (e.g., "DEL") if found, None if not found
    """
    
    url = "https://google-flights2.p.rapidapi.com/api/v1/searchAirport"
    
    querystring = {
        "query": query,
        "language_code": language_code,
        "country_code": country_code
    }
    
    headers = {
        "x-rapidapi-key": "00c4aad806msh8e00931585a4552p1cba4fjsn25893b3ff1c5",
        "x-rapidapi-host": "google-flights2.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        data = response.json()
        
        # Check if the request was successful
        if data.get("status") and data.get("data"):
            # Look for airport in the data
            for item in data["data"]:
                if "list" in item:
                    for airport in item["list"]:
                        if airport.get("type") == "airport" and airport.get("id"):
                            return airport["id"]
        
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except KeyError as e:
        print(f"Unexpected response format: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Example usage:
if __name__ == "__main__":
    # Search for Delhi airport
    airport_id = search_airport_id("del")
    print(f"Airport ID: {airport_id}")  # Should print: Airport ID: DEL
    
    # Search for Los Angeles airport
    airport_id = search_airport_id("Los Angeles")
    print(f"Airport ID: {airport_id}")
    
    # Search for LAX directly
    airport_id = search_airport_id("LAX")
    print(f"Airport ID: {airport_id}")