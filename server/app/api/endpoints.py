from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List, Any
import random
import time

router = APIRouter()

# Schema for the incoming data from the JavaScript frontend
class LocationData(BaseModel):
    latitude: float
    longitude: float

# --- MOCK DATA ---
# This data simulates the output after MongoDB search and AI analysis
MOCK_FOOD = [
    {"name": "Local Street Noodles", "description": "Spicy and famous street vendor dish."},
    {"name": "Artisan Coffee Roasters", "description": "Highly rated, must-try local bean blend."}
]
MOCK_PLACES = [
    {"name": "The Grand Museum", "description": "The city's largest collection of art and history."},
    {"name": "Sunset Lookout Point", "description": "Best panoramic view of the skyline."}
]
MOCK_HOTELS = [
    {"name": "The Luxury Palace Hotel", "rating": 4.9, "price": "$300/night"},
    {"name": "Traveler's Budget Hostel", "rating": 4.1, "price": "$45/night"}
]

@router.post("/recommendations")
def get_recommendations_route(data: LocationData):
    """
    Simulates the AI recommendation process: 
    1. Receives location (data.latitude, data.longitude).
    2. Runs geospatial search (MOCKED).
    3. Calls LLM (MOCKED).
    4. Returns structured results.
    """
    
    print(f"Received location: Lat={data.latitude}, Lon={data.longitude}. Simulating AI search...")
    time.sleep(1.5) # Simulate a network delay for search/AI processing
    
    return {
        "food": MOCK_FOOD,
        "places": MOCK_PLACES,
        "hotels": MOCK_HOTELS
    }