#!/usr/bin/env python3
"""
Flight Search MCP Server
A Model Context Protocol server for searching flights using RapidAPI's Google Flights service.
"""

import requests
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from utils import search_airport_id

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP(name="FlightSearchServer", stateless_http=True)


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


def search_flights_api(request: FlightSearchRequest) -> Dict[str, Any]:
    """
    Search for flights using Google Flights API with Pydantic validation
    
    Args:
        request: Pydantic model containing all search parameters
    
    Returns:
        Flight search results as dictionary
    """
    
    # Get API key from environment (fallback to the one in utils.py)
    api_key = os.getenv("Flight_api", "00c4aad806msh8e00931585a4552p1cba4fjsn25893b3ff1c5")
    
    # Clean input strings
    departure_clean = request.departure_location.strip().strip('"').strip("'")
    arrival_clean = request.arrival_location.strip().strip('"').strip("'")
    
    # Get departure airport ID
    if len(departure_clean) == 3 and departure_clean.isupper():
        departure_id = departure_clean
    else:
        departure_id = search_airport_id(departure_clean, request.language_code, request.country_code, api_key)
        if not departure_id:
            return {"error": f"Could not find departure airport for: {request.departure_location}. Try using the 3-letter airport code (e.g., BOM for Mumbai, DEL for Delhi)"}
    
    # Get arrival airport ID
    if len(arrival_clean) == 3 and arrival_clean.isupper():
        arrival_id = arrival_clean
    else:
        arrival_id = search_airport_id(arrival_clean, request.language_code, request.country_code, api_key)
        if not arrival_id:
            return {"error": f"Could not find arrival airport for: {request.arrival_location}. Try using the 3-letter airport code (e.g., LHR for London, JFK for New York)"}
    
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
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "google-flights2.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status"):
            return data
        else:
            return {"error": f"API request failed: {data.get('message', 'Unknown error')}"}
            
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {e}"}
    except Exception as e:
        return {"error": f"An error occurred: {e}"}


def format_flight_info(flight: Dict[str, Any]) -> str:
    """
    Format flight information for display
    
    Args:
        flight: Flight data dictionary
    
    Returns:
        Formatted flight string
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
    
    # Create formatted output with emojis for better readability
    result = f"🛫 {airline}\n"
    result += f"   🕐 {departure_time} → {arrival_time} ({duration})\n"
    result += f"   💰 ${price}"
    
    if stops == 0:
        result += f" | ✈️ Direct flight"
    elif stops == 1:
        result += f" | 🔄 1 stop{layover_info}"
    else:
        result += f" | 🔄 {stops} stops{layover_info}"
    
    result += f"\n   🎫 Booking: {booking_token[:20]}..." if len(str(booking_token)) > 20 else f"\n   🎫 Booking: {booking_token}"
    
    return result


def format_flight_results(flight_data: Dict[str, Any]) -> str:
    """
    Format flight search results for better readability
    
    Args:
        flight_data: Raw flight data from API
    
    Returns:
        Formatted flight information string
    """
    if "error" in flight_data:
        return f"❌ Error: {flight_data['error']}"
    
    if not flight_data or not flight_data.get("data"):
        return "❌ No flight data available"
    
    data = flight_data["data"]
    formatted_results = []
    
    # Add trip type header
    formatted_results.append("✈️  ONE-WAY FLIGHTS")
    formatted_results.append("=" * 60)
    
    flight_count = 0
    
    if "itineraries" in data:
        itineraries = data["itineraries"]
        
        if "topFlights" in itineraries and itineraries["topFlights"]:
            formatted_results.append("\n🌟 TOP FLIGHT OPTIONS")
            formatted_results.append("-" * 30)
            for i, flight in enumerate(itineraries["topFlights"], 1):
                formatted_results.append(f"\n{i}. {format_flight_info(flight)}")
                flight_count += 1
        
        if "otherFlights" in itineraries and itineraries["otherFlights"]:
            formatted_results.append("\n\n📋 OTHER FLIGHT OPTIONS")
            formatted_results.append("-" * 30)
            for i, flight in enumerate(itineraries["otherFlights"], 1):
                formatted_results.append(f"\n{flight_count + i}. {format_flight_info(flight)}")
    
    elif "topFlights" in data or "otherFlights" in data:
        if "topFlights" in data:
            formatted_results.append("\n🌟 TOP FLIGHT OPTIONS")
            formatted_results.append("-" * 30)
            for i, flight in enumerate(data["topFlights"], 1):
                formatted_results.append(f"\n{i}. {format_flight_info(flight)}")
                flight_count += 1
        
        if "otherFlights" in data:
            formatted_results.append("\n\n📋 OTHER FLIGHT OPTIONS")
            formatted_results.append("-" * 30)
            for i, flight in enumerate(data["otherFlights"], 1):
                formatted_results.append(f"\n{flight_count + i}. {format_flight_info(flight)}")
    
    if flight_count == 0:
        formatted_results.append("\n❌ No flights found for the specified criteria")
    
    return "\n".join(formatted_results)


@mcp.tool(description="Search for one-way flights between two locations")
def search_flights(
    departure_location: str,
    arrival_location: str,
    outbound_date: str,
    travel_class: str = "ECONOMY",
    adults: int = 1,
    children: int = 0,
    infant_on_lap: int = 0,
    infant_in_seat: int = 0,
    show_hidden: int = 0,
    currency: str = "USD",
    language_code: str = "en-US",
    country_code: str = "US"
) -> str:
    """
    Search for one-way flights between two locations.
    
    Args:
        departure_location: Departure city/airport name or IATA code (e.g., "Mumbai", "New York" or "JFK")
        arrival_location: Arrival city/airport name or IATA code (e.g., "Delhi", "London" or "LHR")
        outbound_date: Departure date in YYYY-MM-DD format (must be in the future)
        travel_class: Travel class - ECONOMY, PREMIUM_ECONOMY, BUSINESS, or FIRST (default: ECONOMY)
        adults: Number of adult passengers (age 12+, default: 1)
        children: Number of child passengers (ages 2-11, default: 0)
        infant_on_lap: Number of infants on lap (ages < 2, default: 0)
        infant_in_seat: Number of infants in seat (ages < 2, default: 0)
        show_hidden: Include hidden flights (1=YES, 0=NO, default: 0)
        currency: Currency code for prices (default: USD)
        language_code: Language code for response (default: en-US)
        country_code: Country code for filtering (default: US)
    
    Returns:
        Formatted flight search results including airline, times, duration, price, and stops
    """
    
    try:
        # Create and validate the request using Pydantic
        request = FlightSearchRequest(
            departure_location=departure_location,
            arrival_location=arrival_location,
            outbound_date=outbound_date,
            travel_class=travel_class,
            adults=adults,
            children=children,
            infant_on_lap=infant_on_lap,
            infant_in_seat=infant_in_seat,
            show_hidden=show_hidden,
            currency=currency,
            language_code=language_code,
            country_code=country_code
        )
        
        # Search flights using API
        flight_data = search_flights_api(request)
        
        # Format and return results
        return format_flight_results(flight_data)
        
    except Exception as e:
        return f"❌ Error: {str(e)}"


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()