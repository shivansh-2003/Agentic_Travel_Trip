#!/usr/bin/env python3

"""
Test script for the new web search functionality
"""

import sys
import json
from place_search import PlacesDiscoveryService

def test_web_search():
    """Test the web search functionality"""
    print("🧪 Testing Web Search Functionality")
    print("=" * 40)
    
    discovery = PlacesDiscoveryService()
    location = "Tokyo"
    category = "Natural Attractions"
    
    print(f"🌍 Testing: {category} in {location}")
    print()
    
    # Test each method individually
    print("1️⃣ Testing OpenAI Web Search (new method)...")
    try:
        web_results = discovery.get_places_with_openai_web(location, category)
        print(f"✅ Web Search: Found {len(web_results)} places")
        for i, place in enumerate(web_results[:2], 1):
            print(f"   {i}. {place.get('name', 'N/A')}")
    except Exception as e:
        print(f"❌ Web Search failed: {e}")
    
    print()
    
    print("2️⃣ Testing OpenAI Simple (fallback)...")
    try:
        simple_results = discovery.get_places_with_openai_simple(location, category)
        print(f"✅ Simple Search: Found {len(simple_results)} places")
        for i, place in enumerate(simple_results[:2], 1):
            print(f"   {i}. {place.get('name', 'N/A')}")
    except Exception as e:
        print(f"❌ Simple Search failed: {e}")
    
    print()
    
    print("3️⃣ Testing Full Category Search...")
    try:
        all_results = discovery.categorize_places(location)
        total_categories = len(all_results)
        total_places = sum(len(cat_data['places']) for cat_data in all_results.values())
        
        print(f"✅ Full Search: {total_places} places across {total_categories} categories")
        
        # Show first category as example
        if all_results:
            first_cat = list(all_results.keys())[0]
            first_cat_data = all_results[first_cat]
            print(f"   Example category '{first_cat}': {len(first_cat_data['places'])} places")
            
            # Show data sources
            sources = {}
            for place in first_cat_data['places']:
                source = place.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1
            
            print(f"   Data sources: {dict(sources)}")
        
    except Exception as e:
        print(f"❌ Full Search failed: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("🎯 Test completed!")

if __name__ == "__main__":
    test_web_search() 