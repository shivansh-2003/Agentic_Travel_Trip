import requests
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
from utils import search_airport_id
import os
from dotenv import load_dotenv
load_dotenv()

class FlightSearchRequest(BaseModel):
    """Pydantic model for flight search parameters"""
    # Mandatory fields
    departure_location: str = Field(..., description="Departure city/airport name or IATA code")
    arrival_location: str = Field(..., description="Arrival city/airport name or IATA code")
    outbound_date: str = Field(..., description="Departure date in YYYY-MM-DD format")
    
    # Optional fields with defaults
    travel_class: str = Field("ECONOMY", description="ECONOMY, PREMIUM_ECONOMY, BUSINESS, or FIRST")
    adults: int = Field(1, ge=1, description="Number of adult passengers (age 12+)")
    children: int = Field(0, ge=0, description="Number of child passengers (ages 2-11)")
    infant_on_lap: int = Field(0, ge=0, description="Number of infants on lap (ages < 2)")
    infant_in_seat: int = Field(0, ge=0, description="Number of infants in seat (ages < 2)")
    show_hidden: int = Field(0, ge=0, le=1, description="Include hidden flights (1=YES, 0=NO)")
    currency: str = Field("USD", description="Currency code for prices")
    language_code: str = Field("en-US", description="Language code for response")
    country_code: str = Field("US", description="Country code for filtering")
    api_key: str = Field(os.getenv("Flight_api"), description="RapidAPI key for authentication")
    
    @validator('outbound_date')
    def validate_outbound_date(cls, v):
        try:
            outbound_dt = datetime.strptime(v, '%Y-%m-%d')
            today = datetime.now().date()
            if outbound_dt.date() <= today:
                raise ValueError(f"Outbound date {v} must be in the future")
            return v
        except ValueError as e:
            if "does not match format" in str(e):
                raise ValueError("Invalid date format. Please use YYYY-MM-DD format.")
            raise e
    
    @validator('travel_class')
    def validate_travel_class(cls, v):
        valid_classes = ["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"]
        if v not in valid_classes:
            raise ValueError(f"Travel class must be one of: {', '.join(valid_classes)}")
        return v


def search_flights(request: FlightSearchRequest):
    """
    Search for flights using Google Flights API with Pydantic validation
    
    Args:
        request (FlightSearchRequest): Pydantic model containing all search parameters
    
    Returns:
        dict or None: Flight search results if successful, None if failed
    """
    
    # Get departure airport ID
    if len(request.departure_location) == 3 and request.departure_location.isupper():
        departure_id = request.departure_location
    else:
        departure_id = search_airport_id(request.departure_location, request.language_code, request.country_code, request.api_key)
        if not departure_id:
            print(f"Could not find departure airport for: {request.departure_location}")
            return None
    
    # Get arrival airport ID
    if len(request.arrival_location) == 3 and request.arrival_location.isupper():
        arrival_id = request.arrival_location
    else:
        arrival_id = search_airport_id(request.arrival_location, request.language_code, request.country_code, request.api_key)
        if not arrival_id:
            print(f"Could not find arrival airport for: {request.arrival_location}")
            return None
    
    print(f"Found airports - Departure: {departure_id}, Arrival: {arrival_id}")
    
    # Prepare API request
    url = "https://google-flights2.p.rapidapi.com/api/v1/searchFlights"
    
    querystring = {
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": request.outbound_date,
        "travel_class": request.travel_class,
        "adults": str(request.adults),
        "children": str(request.children),
        "infant_on_lap": str(request.infant_on_lap),
        "infant_in_seat": str(request.infant_in_seat),
        "show_hidden": str(request.show_hidden),
        "currency": request.currency,
        "language_code": request.language_code,
        "country_code": request.country_code
    }
    
    headers = {
        "x-rapidapi-key": request.api_key,
        "x-rapidapi-host": "google-flights2.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status"):
            return data
        else:
            print(f"API request failed: {data.get('message', 'Unknown error')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def format_flight_results(flight_data):
    """
    Format flight search results for better readability
    
    Args:
        flight_data (dict): Raw flight data from API
    
    Returns:
        str: Formatted flight information
    """
    if not flight_data or not flight_data.get("data"):
        return "No flight data available"
    
    data = flight_data["data"]
    formatted_results = []
    
    # Add trip type header
    formatted_results.append("=== ONE-WAY FLIGHTS ===\n")
    
    if "itineraries" in data:
        itineraries = data["itineraries"]
        
        if "topFlights" in itineraries and itineraries["topFlights"]:
            formatted_results.append("=== TOP FLIGHT OPTIONS ===")
            for i, flight in enumerate(itineraries["topFlights"], 1):
                formatted_results.append(f"\n{i}. {format_single_flight(flight)}")
        
        if "otherFlights" in itineraries and itineraries["otherFlights"]:
            formatted_results.append("\n\n=== OTHER FLIGHT OPTIONS ===")
            for i, flight in enumerate(itineraries["otherFlights"], 1):
                formatted_results.append(f"\n{i}. {format_single_flight(flight)}")
        
        if not formatted_results:
            formatted_results.append("No flights found in results")
    
    elif "topFlights" in data or "otherFlights" in data:
        if "topFlights" in data:
            formatted_results.append("=== TOP FLIGHT OPTIONS ===")
            for i, flight in enumerate(data["topFlights"], 1):
                formatted_results.append(f"\n{i}. {format_single_flight(flight)}")
        
        if "otherFlights" in data:
            formatted_results.append("\n\n=== OTHER FLIGHT OPTIONS ===")
            for i, flight in enumerate(data["otherFlights"], 1):
                formatted_results.append(f"\n{i}. {format_single_flight(flight)}")
    else:
        formatted_results.append("Unknown API response format")
    
    return "\n".join(formatted_results)


def format_single_flight(flight):
    """
    Format a single flight entry for one-way flights
    
    Args:
        flight (dict): Single flight data
    
    Returns:
        str: Formatted flight string
    """
    return format_flight_info(flight)


def format_flight_info(flight):
    """
    Format flight information for one-way flights
    
    Args:
        flight (dict): Flight data
    
    Returns:
        str: Formatted flight string
    """
    departure_time = flight.get("departure_time", "N/A")
    arrival_time = flight.get("arrival_time", "N/A")
    duration = flight.get("duration", {}).get("text", "N/A")
    price = flight.get("price", "N/A")
    stops = flight.get("stops", 0)
    booking_token = flight.get("booking_token", "N/A")
    
    # Get airline info
    airline = flight.get("airline", "N/A")
    if airline == "N/A" and flight.get("flights") and len(flight["flights"]) > 0:
        airline = flight["flights"][0].get("airline", "N/A")
    
    # Format layover information
    layover_info = ""
    if flight.get("layovers"):
        layovers = [f"{layover['airport_code']} ({layover['duration_label']})" 
                   for layover in flight["layovers"]]
        layover_info = f" via {', '.join(layovers)}"
    
    # Format flight info
    return (f"Airline: {airline} | "
            f"Departure: {departure_time} | "
            f"Arrival: {arrival_time} | "
            f"Duration: {duration} | "
            f"Price: ${price} | "
            f"Stops: {stops}{layover_info} | "
            f"Booking Token: {booking_token}")



def format_flight_search_results(flight_data, request: FlightSearchRequest):
    """
    Format flight search results for one-way flights
    
    Args:
        flight_data (dict): Raw flight data from API
        request (FlightSearchRequest): The original search request
    
    Returns:
        str: Formatted flight information
    """
    return format_flight_results(flight_data)


if __name__ == "__main__":
    # Test flight search with Pydantic model
    try:
        # Example 1: Minimal required parameters
        search_request = FlightSearchRequest(
            departure_location="JFK",
            arrival_location="LHR", 
            outbound_date="2025-08-15"
        )
        
        print("Testing flight search with minimal parameters:")
        results = search_flights(search_request)
        if results:
            print(format_flight_search_results(results, search_request))
        
        print("\n" + "="*50 + "\n")
        
        # Example 2: With optional parameters
        search_request_advanced = FlightSearchRequest(
            departure_location="New York",
            arrival_location="London",
            outbound_date="2025-08-15",
            travel_class="BUSINESS",
            adults=2,
            children=1
        )
        
        print("Testing flight search with advanced parameters:")
        results_advanced = search_flights(search_request_advanced)
        if results_advanced:
            print(format_flight_search_results(results_advanced, search_request_advanced))
            
    except Exception as e:
        print(f"Validation error: {e}") 