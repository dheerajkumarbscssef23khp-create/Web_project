# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import requests
from a2wsgi import ASGIMiddleware

app = FastAPI(title="Travel Buddy API")

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- MODELS ----------------
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

HEADERS = {"User-Agent": "TravelBuddy/1.0"}

# ---------------- HELPERS ----------------
def get_location_details(lat, lon):
    city = "Nearby Area"
    history = "Explore the local culture and hidden gems."
    image = "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1"

    try:
        geo = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json"},
            headers=HEADERS,
            timeout=5
        ).json()

        address = geo.get("address", {})
        city = address.get("city") or address.get("town") or address.get("village") or city
    except:
        pass

    try:
        search = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "opensearch",
                "search": city,
                "limit": 1,
                "namespace": 0,
                "format": "json",
            },
            timeout=5
        ).json()

        if search and search[1]:
            title = search[1][0]
            wiki = requests.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}",
                timeout=5
            ).json()

            history = wiki.get("extract", history)
            image = (
                wiki.get("originalimage", {}).get("source")
                or wiki.get("thumbnail", {}).get("source")
                or image
            )
    except:
        pass

    return {"city": city, "history": history, "image": image}


def get_weather_and_packing(lat, lon):
    try:
        data = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon, "current_weather": "true"},
            timeout=5
        ).json()

        temp = data.get("current_weather", {}).get("temperature")
        code = data.get("current_weather", {}).get("weathercode")

        packing = ["Water Bottle", "Power Bank"]
        condition = "Pleasant"

        if temp is not None:
            if temp < 15:
                packing.append("Warm Jacket")
                condition = "Cold"
            elif temp > 25:
                packing.append("Sunscreen")
                condition = "Hot"

        if code and code >= 50:
            packing.append("Umbrella")
            condition = "Rainy"

        return {"temp": temp, "condition": condition, "packing": packing}
    except:
        return {"temp": "--", "condition": "Unknown", "packing": ["Essentials"]}


def get_currency(lat, lon):
    try:
        geo = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json"},
            headers=HEADERS,
            timeout=5
        ).json()

        cc = geo.get("address", {}).get("country_code", "us").upper()
        currency_map = {
            "US": "USD", "PK": "PKR", "IN": "INR", "GB": "GBP",
            "AE": "AED", "JP": "JPY", "EU": "EUR"
        }
        currency = currency_map.get(cc, "USD")

        rate = requests.get(
            "https://api.exchangerate-api.com/v4/latest/USD",
            timeout=5
        ).json()["rates"].get(currency, 1)

        return {"currency": currency, "message": f"1 USD ≈ {rate} {currency}"}
    except:
        return {"currency": "USD", "message": "Unavailable"}


def fetch_places(lat, lon, key, value):
    query = f"""
    [out:json];
    node["{key}"="{value}"](around:3000,{lat},{lon});
    out 5;
    """
    try:
        data = requests.get(
            "http://overpass-api.de/api/interpreter",
            params={"data": query},
            timeout=8
        ).json()

        results = []
        for el in data.get("elements", []):
            if "tags" in el and "name" in el["tags"]:
                results.append({
                    "name": el["tags"]["name"],
                    "description": el["tags"].get("amenity", "Local Place").title(),
                    "latitude": el.get("lat"),
                    "longitude": el.get("lon"),
                })
        return results
    except:
        return []


# ---------------- API ----------------
@app.post("/api/recommendations", response_model=RecommendationResponse)
def recommendations(loc: LocationRequest):
    return {
        "location_info": get_location_details(loc.latitude, loc.longitude),
        "weather": get_weather_and_packing(loc.latitude, loc.longitude),
        "currency": get_currency(loc.latitude, loc.longitude),
        "food": fetch_places(loc.latitude, loc.longitude, "amenity", "restaurant"),
        "hotels": fetch_places(loc.latitude, loc.longitude, "tourism", "hotel"),
        "rentacar": [
            {"name": "City Rentals", "price": "$40/day"},
            {"name": "Luxury Wheels", "price": "$120/day"},
        ],
        "safety": [{"name": "Emergency", "description": "Dial 112"}],
        "transport": fetch_places(loc.latitude, loc.longitude, "amenity", "bus_station"),
    }

# ---------------- WSGI ENTRY POINT ----------------
application = ASGIMiddleware(app)
