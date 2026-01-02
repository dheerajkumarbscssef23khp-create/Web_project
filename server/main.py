from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import requests
from a2wsgi import ASGIMiddleware

app = FastAPI(title="Travel Buddy API")

# Use a session for faster consecutive requests
session = requests.Session()
TIMEOUT = 5  # Seconds to wait for any API before giving up

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATA MODELS ---
class LocationRequest(BaseModel):
    latitude: float
    longitude: float

class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: Optional[str] = "View Details"
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class LocationInfo(BaseModel):
    city: str
    history: str
    image: Optional[str] = None

class RecommendationResponse(BaseModel):
    location_info: LocationInfo
    weather: dict
    currency: dict
    food: List[Item]
    hotels: List[Item]
    rentacar: List[Item]
    safety: List[Item]
    transport: List[Item]

# --- HELPERS ---

def get_location_details(lat, lon):
    city = "Unknown Location"
    history = "Explore the local culture and hidden gems of this area."
    image = "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?auto=format&fit=crop&w=1350&q=80"
    
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        headers = {"User-Agent": "TravelBuddy/1.0"}
        resp = session.get(url, params={"lat": lat, "lon": lon, "format": "json"}, headers=headers, timeout=TIMEOUT).json()
        address = resp.get('address', {})
        city = address.get('city') or address.get('town') or address.get('village') or address.get('county') or "Nearby Area"

        if city and city != "Unknown Location":
            search_url = "https://en.wikipedia.org/w/api.php"
            search_params = {"action": "opensearch", "search": city, "limit": 1, "namespace": 0, "format": "json"}
            search_resp = session.get(search_url, params=search_params, timeout=TIMEOUT).json()
            
            if search_resp and len(search_resp) > 1 and len(search_resp[1]) > 0:
                correct_title = search_resp[1][0]
                wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{correct_title}"
                wiki_resp = session.get(wiki_url, timeout=TIMEOUT).json()
                history = wiki_resp.get('extract', history)
                if 'originalimage' in wiki_resp:
                    image = wiki_resp['originalimage']['source']
    except Exception:
        pass
    return {"city": city, "history": history, "image": image}

def get_weather_and_packing(lat, lon):
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {"latitude": lat, "longitude": lon, "current_weather": "true"}
        resp = session.get(url, params=params, timeout=TIMEOUT).json()
        temp = resp.get("current_weather", {}).get("temperature")
        code = resp.get("current_weather", {}).get("weathercode")
        
        packing = ["Water Bottle", "Power Bank"]
        condition = "Pleasant"
        if temp and temp < 15:
            packing.extend(["Warm Jacket", "Scarf"]); condition = "Chilly"
        elif temp and temp > 25:
            packing.extend(["Sunscreen", "Hat"]); condition = "Warm"
        
        return {"temp": temp, "condition": condition, "packing": packing}
    except:
        return {"temp": "--", "condition": "Unknown", "packing": ["Essentials"]}

def get_country_and_currency(lat, lon):
    try:
        geo_url = "https://nominatim.openstreetmap.org/reverse"
        headers = {"User-Agent": "TravelBuddy/1.0"}
        geo_data = session.get(geo_url, params={"lat": lat, "lon": lon, "format": "json"}, headers=headers, timeout=TIMEOUT).json()
        country_code = geo_data.get("address", {}).get("country_code", "us").upper()
        
        rate_url = "https://api.exchangerate-api.com/v4/latest/USD"
        rate_data = session.get(rate_url, timeout=TIMEOUT).json()
        local_cur = {"PK": "PKR", "IN": "INR", "JP": "JPY"}.get(country_code, "USD")
        rate = rate_data.get("rates", {}).get(local_cur, 1.0)
        
        return {"currency": local_cur, "message": f"1 USD ≈ {rate} {local_cur}"}
    except:
        return {"currency": "USD", "message": "Rate Unavailable"}

def fetch_overpass_data(lat, lon, key, value, radius=5000, limit=5):
    url = "http://overpass-api.de/api/interpreter"
    query = f'[out:json];(node["{key}"="{value}"](around:{radius},{lat},{lon});way["{key}"="{value}"](around:{radius},{lat},{lon}););out center {limit};'
    try:
        response = session.get(url, params={'data': query}, timeout=TIMEOUT)
        data = response.json()
        results = []
        for el in data.get('elements', []):
            tags = el.get('tags', {})
            results.append({
                "name": tags.get('name', 'Local Spot'),
                "description": tags.get('cuisine', tags.get('addr:street', 'Nearby')).capitalize(),
                "price": "View Details",
                "latitude": el.get('lat') or el.get('center', {}).get('lat'),
                "longitude": el.get('lon') or el.get('center', {}).get('lon')
            })
        return results
    except:
        return []

# --- MAIN API ENDPOINT ---
@app.post("/api/recommendations", response_model=RecommendationResponse)
def get_recommendations(loc: LocationRequest):
    # Fetching metadata
    loc_info = get_location_details(loc.latitude, loc.longitude)
    weather = get_weather_and_packing(loc.latitude, loc.longitude)
    currency = get_country_and_currency(loc.latitude, loc.longitude)

    # Fetching place data
    food = fetch_overpass_data(loc.latitude, loc.longitude, "amenity", "restaurant")
    hotels = fetch_overpass_data(loc.latitude, loc.longitude, "tourism", "hotel")
    safety = fetch_overpass_data(loc.latitude, loc.longitude, "amenity", "hospital", limit=3)
    transport = fetch_overpass_data(loc.latitude, loc.longitude, "public_transport", "station", radius=3000)

    rentals = [
        {"name": "City Cruisers", "description": "Economy Sedans", "price": "$40/day", "latitude": loc.latitude + 0.005, "longitude": loc.longitude + 0.005},
        {"name": "Luxury Wheels", "description": "SUVs & Sports", "price": "$120/day", "latitude": loc.latitude - 0.005, "longitude": loc.longitude - 0.005}
    ]

    return {
        "location_info": loc_info, "weather": weather, "currency": currency,
        "food": food or [{"name": "No data found", "description": "Try searching a larger area"}],
        "hotels": hotels or [{"name": "No data found", "description": "Try searching a larger area"}],
        "rentacar": rentals,
        "safety": safety or [{"name": "Emergency Services", "description": "Dial 112 or 911"}],
        "transport": transport or [{"name": "No major stations", "description": "Look for local transport"}]
    }

# PythonAnywhere WSGI Wrapper
wsgi_app = ASGIMiddleware(app)# --- HOW TO RUN ---
# Terminal command: uvicorn main:app --reload
