import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")

# Predefined Categories
CATEGORIES = {
    "natural_attractions": "🏞️ Natural Attractions (parks, beaches, mountains, waterfalls)",
    "cultural_heritage": "🏛️ Cultural & Heritage (museums, temples, historical sites)",
    "urban_modern": "🏙️ Urban & Modern (skyscrapers, shopping, theaters)",
    "adventure_outdoor": "🏔️ Adventure & Outdoor (trekking, diving, extreme sports)",
    "recreation_leisure": "🎢 Recreation & Leisure (theme parks, zoos, spas)",
    "sports_events": "🏟️ Sports & Events (stadiums, festivals, sporting venues)",
    "health_wellness": "🧘‍♀️ Health & Wellness (spas, wellness centers, medical tourism)",
    "religious_spiritual": "🕉️ Religious & Spiritual (pilgrimage sites, sacred places)",
    "educational_scientific": "🔬 Educational & Scientific (science centers, universities)",
    "special_interest": "🍷 Special Interest (culinary tours, photography, niche tourism)"
}