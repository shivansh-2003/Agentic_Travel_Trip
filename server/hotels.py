#!/usr/bin/env python3
"""
Hotel Booking MCP Server
A Model Context Protocol server for searching hotel bookings using RapidAPI's Booking service.
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI
# Initialize FastMCP server
mcp = FastMCP(name="HotelBookingServer", stateless_http=True)
import os
from dotenv import load_dotenv
load_dotenv()



# Configuration
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST")
BASE_URL = os.getenv("BASE_URL")

def search_hotels_api(location: str, checkin_date: str, checkout_date: str) -> Dict[str, Any]:
    """
    Make API request to search hotels
    
    Args:
        location: Location to search (e.g., "delhi")
        checkin_date: Check-in date in YYYY-MM-DD format
        checkout_date: Check-out date in YYYY-MM-DD format
    
    Returns:
        API response as dictionary
    """
    # Prepare request parameters
    querystring = {
        "location": location,
        "checkin_date": checkin_date,
        "checkout_date": checkout_date
    }
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    
    try:
        # Make the API request
        response = requests.get(BASE_URL, headers=headers, params=querystring)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"API request failed with status code: {response.status_code}",
                "response": response.text
            }
            
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse JSON response: {str(e)}"}

def format_hotels_response(data: Dict[str, Any]) -> str:
    """
    Format hotel search results into readable string
    
    Args:
        data: API response data
        
    Returns:
        Formatted string with hotel results
    """
    if "error" in data:
        return f"❌ Error: {data['error']}"
    
    if not data.get("status"):
        return f"❌ API returned error: {data.get('message', 'Unknown error')}"
    
    hotels = data.get("data", [])
    total_count = data.get("totalResultCount", 0)
    
    if not hotels:
        return "❌ No hotels found for the specified search criteria"
    
    result = f"🏨 Found {total_count} hotels:\n"
    result += "=" * 60 + "\n\n"
    
    for i, hotel in enumerate(hotels, 1):
        name = hotel.get("name", "Unknown Hotel")
        
        # Get price info
        price_info = hotel.get("priceBreakdown", {})
        gross_price = price_info.get("grossPrice", {})
        price = gross_price.get("amountRounded", "N/A")
        currency = gross_price.get("currency", "")
        
        # Get rating
        rating = hotel.get("reviewScore", 0)
        review_word = hotel.get("reviewScoreWord", "")
        review_count = hotel.get("reviewCount", 0)
        
        # Get location
        location = hotel.get("wishlistName", "")
        country = hotel.get("countryCode", "").upper()
        
        # Check-in/out times
        checkin_time = hotel.get("checkin", {}).get("fromTime", "N/A")
        checkout_time = hotel.get("checkout", {}).get("untilTime", "N/A")
        
        result += f"{i}. {name}\n"
        result += f"   💰 Price: {price} {currency} (total stay)\n"
        
        if rating > 0:
            result += f"   ⭐ Rating: {rating}/10 ({review_word}) - {review_count} reviews\n"
        else:
            result += f"   ⭐ No reviews yet\n"
            
        if location:
            result += f"   📍 Location: {location}, {country}\n"
            
        result += f"   🕐 Check-in: {checkin_time} | Check-out: {checkout_time}\n\n"
    
    return result

@mcp.tool(description="Search for hotel bookings by location and dates")
def search_hotels(location: str, checkin_date: str, checkout_date: str) -> str:
    """
    Search for hotel bookings in a specific location for given dates.
    
    Args:
        location: Location to search for hotels (e.g., "delhi", "mumbai", "goa")
        checkin_date: Check-in date in YYYY-MM-DD format (e.g., "2025-06-27")
        checkout_date: Check-out date in YYYY-MM-DD format (e.g., "2025-07-05")
    
    Returns:
        Formatted string with hotel search results
    """
    
    # Validate date format
    try:
        checkin = datetime.strptime(checkin_date, "%Y-%m-%d")
        checkout = datetime.strptime(checkout_date, "%Y-%m-%d")
        
        if checkin >= checkout:
            return "❌ Error: Check-in date must be before check-out date"
        
        if checkin < datetime.now():
            return "❌ Error: Check-in date cannot be in the past"
            
    except ValueError:
        return "❌ Error: Invalid date format. Please use YYYY-MM-DD format (e.g., 2025-06-27)"
    
    # Search hotels using API
    result = search_hotels_api(location, checkin_date, checkout_date)
    
    # Format and return results
    return format_hotels_response(result)