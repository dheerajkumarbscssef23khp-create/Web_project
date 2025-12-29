from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import requests

app = FastAPI(title="Travel Buddy API")

# --- CORS SETTINGS ---
# Allows your HTML frontend to communicate with this Python backend
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

# --- HELPER 1: Smart Location Details (Wikipedia + OpenStreetMap) ---
def get_location_details(lat, lon):
    city = "Unknown Location"
    history = "Explore the local culture and hidden gems of this area."
    # Default fallback image
    image = "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?auto=format&fit=crop&w=1350&q=80" 
    
    try:
        # 1. Reverse Geocode to get the City Name
        url = "https://nominatim.openstreetmap.org/reverse"
        headers = {"User-Agent": "TravelBuddy/1.0"}
        resp = requests.get(url, params={"lat": lat, "lon": lon, "format": "json"}, headers=headers).json()
        address = resp.get('address', {})
        
        # Prioritize City -> Town -> Village -> County
        city = address.get('city') or address.get('town') or address.get('village') or address.get('county') or "Nearby Area"
    except:
        pass

    if city and city != "Unknown Location":
        try:
            # 2. Smart Wikipedia Search
            # First, search for the best matching article title (e.g., "Khairpur" -> "Khairpur, Pakistan")
            search_url = "https://en.wikipedia.org/w/api.php"
            search_params = {
                "action": "opensearch",
                "search": city,
                "limit": 1,
                "namespace": 0,
                "format": "json"
            }
            search_resp = requests.get(search_url, params=search_params).json()
            
            # If a matching article is found, use that specific title
            if search_resp and len(search_resp) > 1 and len(search_resp[1]) > 0:
                correct_title = search_resp[1][0] 
                
                # 3. Get Summary & Image using the CORRECT title
                wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{correct_title}"
                wiki_resp = requests.get(wiki_url).json()
                
                if 'extract' in wiki_resp:
                    history = wiki_resp['extract']
                
                if 'originalimage' in wiki_resp:
                    image = wiki_resp['originalimage']['source']
                elif 'thumbnail' in wiki_resp:
                    image = wiki_resp['thumbnail']['source']
        except Exception as e:
            print(f"Wiki Error: {e}")

    return {"city": city, "history": history, "image": image}

# --- HELPER 2: Weather & Smart Packing ---
def get_weather_and_packing(lat, lon):
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {"latitude": lat, "longitude": lon, "current_weather": "true"}
        resp = requests.get(url, params=params).json()
        
        temp = resp.get("current_weather", {}).get("temperature")
        weather_code = resp.get("current_weather", {}).get("weathercode")
        
        packing_list = ["Water Bottle", "Power Bank"]
        condition = "Pleasant"
        
        if temp is not None:
            if temp < 15:
                packing_list.extend(["Warm Jacket", "Scarf"])
                condition = "Chilly"
            elif temp > 25:
                packing_list.extend(["Sunscreen", "Hat", "Sunglasses"])
                condition = "Warm"
            
            # WMO Weather Codes for Rain
            if weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82, 95]:
                packing_list.append("Umbrella ☔")
                condition = "Rainy"
            elif weather_code <= 3:
                condition = "Clear/Cloudy"
                
        return {"temp": temp, "condition": condition, "packing": packing_list}
    except:
        return {"temp": "--", "condition": "Unknown", "packing": ["Essentials"]}

# --- HELPER 3: Currency Converter ---
def get_country_and_currency(lat, lon):
    try:
        geo_url = "https://nominatim.openstreetmap.org/reverse"
        headers = {"User-Agent": "TravelBuddy/1.0"}
        geo_data = requests.get(geo_url, params={"lat": lat, "lon": lon, "format": "json"}, headers=headers).json()
        country_code = geo_data.get("address", {}).get("country_code", "us").upper()
        
        currency_map = {
            "US": "USD", "GB": "GBP", "FR": "EUR", "DE": "EUR", "IT": "EUR", "ES": "EUR", 
            "PK": "PKR", "IN": "INR", "JP": "JPY", "AE": "AED", "CA": "CAD", "AU": "AUD"
        }
        local_currency = currency_map.get(country_code, "USD")
        
        # Free Currency API
        rate_url = "https://api.exchangerate-api.com/v4/latest/USD"
        rate_data = requests.get(rate_url).json()
        rate = rate_data.get("rates", {}).get(local_currency, 1.0)
        
        return {
            "currency": local_currency,
            "message": f"1 USD ≈ {rate} {local_currency}"
        }
    except:
        return {"currency": "USD", "message": "Rate Unavailable"}

# --- HELPER 4: Map Data (Overpass API) ---
def fetch_overpass_data(lat, lon, key, value, radius=5000, limit=5):
    url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    (
      node["{key}"="{value}"](around:{radius},{lat},{lon});
      way["{key}"="{value}"](around:{radius},{lat},{lon});
    );
    out center {limit};
    """
    try:
        response = requests.get(url, params={'data': query}, timeout=20)
        data = response.json()
        results = []
        
        for el in data.get('elements', []):
            tags = el.get('tags', {})
            item_lat = el.get('lat') or el.get('center', {}).get('lat')
            item_lon = el.get('lon') or el.get('center', {}).get('lon')

            if 'name' in tags:
                results.append({
                    "name": tags['name'],
                    "description": tags.get('cuisine', tags.get('addr:street', 'Local Spot')).capitalize(),
                    "price": "View Details",
                    "latitude": item_lat,
                    "longitude": item_lon
                })
        return results
    except:
        return []

# --- MAIN API ENDPOINT ---
@app.post("/api/recommendations", response_model=RecommendationResponse)
async def get_recommendations(loc: LocationRequest):
    print(f"Processing Request for: {loc.latitude}, {loc.longitude}")

    # 1. Fetch Meta Data (History, Weather, Currency)
    loc_info = get_location_details(loc.latitude, loc.longitude)
    weather_data = get_weather_and_packing(loc.latitude, loc.longitude)
    currency_data = get_country_and_currency(loc.latitude, loc.longitude)

    # 2. Fetch Real Places (Hotels & Food)
    food = fetch_overpass_data(loc.latitude, loc.longitude, "amenity", "restaurant")
    hotels = fetch_overpass_data(loc.latitude, loc.longitude, "tourism", "hotel")
    
    # 3. Fetch Safety (Hospitals & Pharmacies)
    hospitals = fetch_overpass_data(loc.latitude, loc.longitude, "amenity", "hospital", limit=3)
    pharmacies = fetch_overpass_data(loc.latitude, loc.longitude, "amenity", "pharmacy", limit=3)
    safety_items = hospitals + pharmacies

    # 4. Fetch Public Transport
    transport = fetch_overpass_data(loc.latitude, loc.longitude, "public_transport", "station", radius=3000)
    if not transport:
        # Fallback to bus stations if no generic 'station' found
        transport = fetch_overpass_data(loc.latitude, loc.longitude, "amenity", "bus_station", radius=3000)

    # 5. Mock Rentals (with valid nearby coordinates)
    rentals = [
        {"name": "City Cruisers", "description": "Economy Sedans", "price": "$40/day", "latitude": loc.latitude + 0.005, "longitude": loc.longitude + 0.005},
        {"name": "Luxury Wheels", "description": "SUVs & Sports", "price": "$120/day", "latitude": loc.latitude - 0.005, "longitude": loc.longitude - 0.005}
    ]

    return {
        "location_info": loc_info,
        "weather": weather_data,
        "currency": currency_data,
        "food": food if food else [{"name": "No data found", "description": "Try searching a larger city area"}],
        "hotels": hotels if hotels else [{"name": "No data found", "description": "Try searching a larger city area"}],
        "rentacar": rentals,
        "safety": safety_items if safety_items else [{"name": "Emergency Services", "description": "Dial 112 or 911"}],
        "transport": transport if transport else [{"name": "No major stations", "description": "Look for local taxis/rickshaws"}]
    }

# --- HOW TO RUN ---
# Terminal command: uvicorn main:app --reload