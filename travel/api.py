from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from main import TravelAssistant
from config import CATEGORIES

app = FastAPI(
    title="Travel Recommendations API",
    description="Get travel recommendations for any location with selected categories",
    version="1.0.0"
)

# Request model
class TravelRequest(BaseModel):
    place_name: str
    categories: Optional[List[str]] = None  # If None, will use default categories
    
    class Config:
        schema_extra = {
            "example": {
                "place_name": "Tokyo",
                "categories": ["natural_attractions", "cultural_heritage", "urban_modern"]
            }
        }

# Response model
class TravelResponse(BaseModel):
    place_name: str
    selected_categories: List[str]
    recommendations: Dict[str, Any]
    timestamp: str

# Initialize the travel assistant
travel_assistant = TravelAssistant()

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Travel Recommendations API",
        "version": "1.0.0",
        "endpoints": {
            "get_recommendations": "/recommendations",
            "available_categories": "/categories",
            "health": "/health"
        }
    }

@app.get("/categories")
async def get_available_categories():
    """Get all available categories"""
    return {
        "categories": CATEGORIES,
        "category_keys": list(CATEGORIES.keys()),
        "total": len(CATEGORIES)
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/recommendations", response_model=TravelResponse)
async def get_travel_recommendations(request: TravelRequest):
    """
    Get travel recommendations for a place with selected categories
    
    - **place_name**: Name of the city or location to explore
    - **categories**: List of category keys to search (optional, defaults to natural_attractions, cultural_heritage, urban_modern)
    
    Returns recommendations in the format:
    ```json
    {
        "category_name": [
            {
                "tourist_place_name": "Place Name",
                "tourist_description": "Description",
                "place_image_url": "image_url"
            }
        ]
    }
    ```
    """
    try:
        # Validate place name
        if not request.place_name or not request.place_name.strip():
            raise HTTPException(status_code=400, detail="Place name is required")
        
        place_name = request.place_name.strip()
        
        # Handle categories
        if request.categories:
            # Validate categories
            invalid_categories = [cat for cat in request.categories if cat not in CATEGORIES]
            if invalid_categories:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid categories: {invalid_categories}. Available categories: {list(CATEGORIES.keys())}"
                )
            selected_categories = request.categories
        else:
            # Default categories
            category_keys = list(CATEGORIES.keys())
            selected_categories = [category_keys[0], category_keys[1], category_keys[2]]  # natural, cultural, urban
        
        # Generate recommendations
        recommendations = travel_assistant.generate_travel_recommendations(
            location=place_name,
            selected_categories=selected_categories
        )
        
        # Prepare response
        response = TravelResponse(
            place_name=place_name,
            selected_categories=selected_categories,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat()
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/recommendations/{place_name}")
async def get_recommendations_by_path(
    place_name: str, 
    categories: Optional[str] = None
):
    """
    Alternative endpoint: Get recommendations using path parameter
    
    - **place_name**: Name of the city or location
    - **categories**: Comma-separated category keys (optional)
    
    Example: /recommendations/Tokyo?categories=natural_attractions,cultural_heritage
    """
    # Parse categories from query parameter
    category_list = None
    if categories:
        category_list = [cat.strip() for cat in categories.split(',') if cat.strip()]
    
    # Create request object and reuse main endpoint logic
    request = TravelRequest(place_name=place_name, categories=category_list)
    return await get_travel_recommendations(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 