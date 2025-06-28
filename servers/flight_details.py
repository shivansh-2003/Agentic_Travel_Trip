import requests
from typing import Optional
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

load_dotenv()


class FlightBookingDetailsRequest(BaseModel):
    """Pydantic model for flight booking details parameters"""
    # Mandatory field
    booking_token: str = Field(..., description="A unique identifier from flight search results for retrieving booking details")
    
    # Optional fields with defaults
    currency: str = Field("USD", description="Currency code for price formatting")
    language_code: str = Field("en-US", description="Language code for response")
    country_code: str = Field("US", description="Country code for filtering")
    api_key: str = Field(os.getenv("Flight_api"), description="RapidAPI key for authentication")


def get_booking_details(request: FlightBookingDetailsRequest):
    """
    Get flight booking details using Google Flights API with Pydantic validation
    
    Args:
        request (FlightBookingDetailsRequest): Pydantic model containing all booking parameters
    
    Returns:
        dict or None: Flight booking details if successful, None if failed
    """
    
    # Prepare API request
    url = "https://google-flights2.p.rapidapi.com/api/v1/getBookingDetails"
    
    querystring = {
        "booking_token": request.booking_token,
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


def format_booking_details(booking_data):
    """
    Format flight booking details for better readability
    
    Args:
        booking_data (dict): Raw booking data from API
    
    Returns:
        str: Formatted booking information
    """
    if not booking_data or not booking_data.get("data"):
        return "No booking data available"
    
    data = booking_data["data"]
    formatted_results = []
    
    # Add booking details header
    formatted_results.append("=== FLIGHT BOOKING DETAILS ===\n")
    
    # Extract basic booking information
    if "flight_details" in data:
        flight_details = data["flight_details"]
        formatted_results.append(format_flight_booking_info(flight_details))
    
    # Extract pricing information
    if "pricing" in data:
        pricing = data["pricing"]
        formatted_results.append(f"\n=== PRICING INFORMATION ===")
        formatted_results.append(format_pricing_info(pricing))
    
    # Extract booking options
    if "booking_options" in data:
        booking_options = data["booking_options"]
        formatted_results.append(f"\n=== BOOKING OPTIONS ===")
        for i, option in enumerate(booking_options, 1):
            formatted_results.append(f"\n{i}. {format_booking_option(option)}")
    
    # Extract terms and conditions
    if "terms" in data:
        terms = data["terms"]
        formatted_results.append(f"\n=== TERMS & CONDITIONS ===")
        formatted_results.append(format_terms_info(terms))
    
    return "\n".join(formatted_results)


def format_flight_booking_info(flight_details):
    """
    Format flight booking information
    
    Args:
        flight_details (dict): Flight details data
    
    Returns:
        str: Formatted flight booking string
    """
    info_lines = []
    
    if "departure" in flight_details:
        departure = flight_details["departure"]
        info_lines.append(f"Departure: {departure.get('airport', 'N/A')} at {departure.get('time', 'N/A')}")
    
    if "arrival" in flight_details:
        arrival = flight_details["arrival"]
        info_lines.append(f"Arrival: {arrival.get('airport', 'N/A')} at {arrival.get('time', 'N/A')}")
    
    if "duration" in flight_details:
        info_lines.append(f"Duration: {flight_details['duration']}")
    
    if "airline" in flight_details:
        info_lines.append(f"Airline: {flight_details['airline']}")
    
    if "flight_number" in flight_details:
        info_lines.append(f"Flight Number: {flight_details['flight_number']}")
    
    return "\n".join(info_lines)


def format_pricing_info(pricing):
    """
    Format pricing information
    
    Args:
        pricing (dict): Pricing data
    
    Returns:
        str: Formatted pricing string
    """
    price_lines = []
    
    if "total_price" in pricing:
        price_lines.append(f"Total Price: {pricing['total_price']}")
    
    if "base_price" in pricing:
        price_lines.append(f"Base Price: {pricing['base_price']}")
    
    if "taxes_and_fees" in pricing:
        price_lines.append(f"Taxes & Fees: {pricing['taxes_and_fees']}")
    
    if "currency" in pricing:
        price_lines.append(f"Currency: {pricing['currency']}")
    
    return "\n".join(price_lines)


def format_booking_option(option):
    """
    Format a single booking option
    
    Args:
        option (dict): Booking option data
    
    Returns:
        str: Formatted booking option string
    """
    option_lines = []
    
    if "provider" in option:
        option_lines.append(f"Provider: {option['provider']}")
    
    if "price" in option:
        option_lines.append(f"Price: {option['price']}")
    
    if "booking_url" in option:
        option_lines.append(f"Booking URL: {option['booking_url']}")
    
    if "features" in option:
        features = ", ".join(option['features'])
        option_lines.append(f"Features: {features}")
    
    return " | ".join(option_lines)


def format_terms_info(terms):
    """
    Format terms and conditions information
    
    Args:
        terms (dict): Terms data
    
    Returns:
        str: Formatted terms string
    """
    terms_lines = []
    
    if "cancellation_policy" in terms:
        terms_lines.append(f"Cancellation Policy: {terms['cancellation_policy']}")
    
    if "baggage_policy" in terms:
        terms_lines.append(f"Baggage Policy: {terms['baggage_policy']}")
    
    if "change_policy" in terms:
        terms_lines.append(f"Change Policy: {terms['change_policy']}")
    
    return "\n".join(terms_lines)


def extract_token_price_website(booking_data, booking_token=None):
    """
    Extract specific information: token, price, and website from booking details
    
    Args:
        booking_data (dict): Raw booking data from API response
        booking_token (str, optional): The booking token used for the request
    
    Returns:
        dict: Dictionary containing token, price, and website information
    """
    result = {
        "token": booking_token or "N/A",
        "price": "N/A",
        "website": "N/A"
    }
    
    if not booking_data:
        return result
    
    # Check if this is the flight search results format (like result.json)
    if "price" in booking_data and "website" in booking_data and "token" in booking_data:
        result["price"] = booking_data["price"]
        result["website"] = booking_data["website"]
        result["token"] = booking_data["token"]
        return result
    
    # Handle API booking details response structure
    if not booking_data.get("data"):
        return result
    
    data = booking_data["data"]
    
    # Check if data is a list (multiple items) or a single dictionary
    if isinstance(data, list):
        # If it's a list, take the first item or search through items
        if not data:
            return result
        # Try to find the item with price/website info, or use the first one
        data_item = data[0]
        for item in data:
            if isinstance(item, dict) and ("price" in item or "pricing" in item):
                data_item = item
                break
        data = data_item
    
    # Now data should be a dictionary, proceed with extraction
    if not isinstance(data, dict):
        return result
    
    # Look for price in multiple possible locations
    price_locations = [
        lambda d: d.get("pricing", {}).get("total_price"),
        lambda d: d.get("pricing", {}).get("price"), 
        lambda d: d.get("price"),
        lambda d: d.get("booking_options", [{}])[0].get("price") if d.get("booking_options") else None,
        lambda d: d.get("flight_details", {}).get("price")
    ]
    
    for get_price in price_locations:
        try:
            price = get_price(data)
            if price is not None:
                result["price"] = price
                break
        except (KeyError, IndexError, TypeError):
            continue
    
    # Look for website/booking URL in multiple possible locations
    website_locations = [
        lambda d: d.get("booking_options", [{}])[0].get("booking_url") if d.get("booking_options") else None,
        lambda d: d.get("booking_options", [{}])[0].get("url") if d.get("booking_options") else None,
        lambda d: d.get("booking_url"),
        lambda d: d.get("url"),
        lambda d: d.get("website")
    ]
    
    for get_website in website_locations:
        try:
            website = get_website(data)
            if website is not None:
                result["website"] = website
                break
        except (KeyError, IndexError, TypeError):
            continue
    
    # If we still don't have website info, try to extract from other nested structures
    if result["website"] == "N/A":
        try:
            # Check if there are flight segments with airline websites
            if isinstance(data, list):
                for item in data:
                    if "website" in item:
                        result["website"] = item["website"]
                        break
            elif "flights" in data:
                flights = data["flights"]
                if isinstance(flights, list) and flights:
                    first_flight = flights[0]
                    if "website" in first_flight:
                        result["website"] = first_flight["website"]
        except (KeyError, TypeError):
            pass
    
    return result



def print_token_price_website(token_info):
    """
    Print token, price, and website information in a clean format
    
    Args:
        token_info (dict): Dictionary containing token, price, and website info
    """
    print("\n" + "="*50)
    print("BOOKING DETAILS SUMMARY")
    print("="*50)
    print(f"Token: {token_info['token']}")
    print(f"Price: {token_info['price']}")
    print(f"Website: {token_info['website']}")
    print("="*50)


# Example usage function
def example_booking_details_search():
    """
    Example function demonstrating how to use the booking details functionality
    """
    # Example booking token (this would come from a flight search result)
    booking_token = "W1syLDEsWyIxIiwiMCIsIjAiLCIwIl1dLFsiMjAyNS0wOC0xNSIsIkpGSyIsIkxIUiIsW1siSkZLIiwiMjAyNS0wOC0xNSIsIkxIUiIsIkFBIiwiMTAwIl1dXV0="
    
    request = FlightBookingDetailsRequest(
        booking_token=booking_token,
        currency="USD",
        language_code="en-US",
        country_code="US"
    )
    
    print("Searching for booking details...")
    booking_data = get_booking_details(request)
    
    if booking_data:
        print("Booking details found!")
        
        # Extract and display token, price, and website
        token_info = extract_token_price_website(booking_data, booking_token)
        print_token_price_website(token_info)
        
        # Also print full formatted results if needed
        print("\n" + "="*50)
        print("FULL BOOKING DETAILS")
        print("="*50)
        formatted_results = format_booking_details(booking_data)
        print(formatted_results)
        
        return token_info
    else:
        print("No booking details found or API error occurred.")
        return None


if __name__ == "__main__":
    # Run example search when script is executed directly
    example_booking_details_search()
