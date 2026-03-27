import time
from typing import Dict, List

import requests

from processors.category_filter import map_osm_category

OVERPASS_API_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
REQUEST_TIMEOUT_SECONDS = 45
MAX_RETRIES_PER_ENDPOINT = 2


def get_mock_osm_data() -> List[Dict]:
    """Return mock OpenStreetMap shop data for testing/fallback."""
    return [
        {
            "name": "Sample OSM Shop 1",
            "address": "789 Clementi Road, Singapore",
            "lat": 1.3315,
            "lng": 103.7623,
            "phone": "+65 6777 1234",
            "opening_hours": "09:00-21:00",
            "shop_type": "grocery_store",
            "source": "osm",
        },
        {
            "name": "Sample OSM Shop 2",
            "address": "321 Jurong East, Singapore",
            "lat": 1.3368,
            "lng": 103.7425,
            "phone": "+65 6898 5678",
            "opening_hours": "10:00-22:00",
            "shop_type": "shopping_mall",
            "source": "osm",
        },
    ]


def fetch_osm_shops(use_mock: bool = False, allow_mock_fallback: bool = False) -> List[Dict]:
    """Fetch challenge-category places from OpenStreetMap with endpoint failover."""

    if use_mock:
        print("Info: Using mock OpenStreetMap data")
        return get_mock_osm_data()

    query = """
    [out:json][timeout:25];
    area["ISO3166-1"="SG"][admin_level=2]->.sg;
    (
      node["amenity"="restaurant"](area.sg);
      node["amenity"="cafe"](area.sg);
      node["amenity"="pharmacy"](area.sg);
      node["amenity"="fuel"](area.sg);
      node["tourism"="attraction"](area.sg);
      node["tourism"="hotel"](area.sg);
      node["leisure"="amusement_park"](area.sg);
      node["shop"="mall"](area.sg);
      node["shop"="department_store"](area.sg);
      node["shop"="supermarket"](area.sg);
      node["shop"="convenience"](area.sg);
      way["amenity"="restaurant"](area.sg);
      way["amenity"="cafe"](area.sg);
      way["amenity"="pharmacy"](area.sg);
      way["amenity"="fuel"](area.sg);
      way["tourism"="attraction"](area.sg);
      way["tourism"="hotel"](area.sg);
      way["leisure"="amusement_park"](area.sg);
      way["shop"="mall"](area.sg);
      way["shop"="department_store"](area.sg);
      way["shop"="supermarket"](area.sg);
      way["shop"="convenience"](area.sg);
    );
    out center;
    """

    for endpoint in OVERPASS_API_URLS:
        for attempt in range(MAX_RETRIES_PER_ENDPOINT):
            try:
                response = requests.post(
                    endpoint,
                    data=query,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                    headers={"Content-Type": "application/osm3s"},
                )

                if response.status_code in (429, 500, 502, 503, 504):
                    sleep_seconds = 2 ** attempt
                    print(
                        f"Warning: OSM endpoint {endpoint} returned {response.status_code}. "
                        f"Retrying in {sleep_seconds}s..."
                    )
                    time.sleep(sleep_seconds)
                    continue

                response.raise_for_status()
                data = response.json()

                places = []
                for element in data.get("elements", []):
                    place = _parse_osm_element(element)
                    if place:
                        places.append(place)

                print(f"Success: Fetched {len(places)} records from OpenStreetMap via {endpoint}")
                if places:
                    return places

                print(f"Info: OSM returned 0 records via {endpoint}")
                break

            except requests.exceptions.RequestException as e:
                print(f"Warning: Error fetching OSM data from {endpoint}: {e}")
                sleep_seconds = 2 ** attempt
                time.sleep(sleep_seconds)

    print("Warning: All OSM endpoints failed or returned no data")
    return get_mock_osm_data() if allow_mock_fallback else []


def _parse_osm_element(element: Dict) -> Dict:
    """Parse OSM element into standardized format."""
    tags = element.get("tags", {})

    lat = element.get("lat")
    lon = element.get("lon")

    if "center" in element:
        lat = element["center"].get("lat")
        lon = element["center"].get("lon")

    if not lat or not lon:
        return None

    category = map_osm_category(tags)
    if not category:
        return None

    return {
        "name": tags.get("name", "Unknown Place"),
        "address": tags.get("addr:full") or tags.get("addr:street") or "Unknown Address",
        "lat": lat,
        "lng": lon,
        "source": "osm",
        "shop_type": category,
        "phone": tags.get("phone"),
        "website": tags.get("website"),
        "opening_hours": tags.get("opening_hours"),
    }
