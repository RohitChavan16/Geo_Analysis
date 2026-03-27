import time
from typing import Dict, List

import requests

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
            "shop_type": "general",
            "source": "osm",
        },
        {
            "name": "Sample OSM Shop 2",
            "address": "321 Jurong East, Singapore",
            "lat": 1.3368,
            "lng": 103.7425,
            "phone": "+65 6898 5678",
            "opening_hours": "10:00-22:00",
            "shop_type": "general",
            "source": "osm",
        },
    ]


def fetch_osm_shops(use_mock: bool = False, allow_mock_fallback: bool = False) -> List[Dict]:
    """Fetch shops from OpenStreetMap using Overpass API with endpoint failover."""

    if use_mock:
        print("Info: Using mock OpenStreetMap data")
        return get_mock_osm_data()

    # Restrict strictly to Singapore administrative area.
    query = """
    [out:json][timeout:25];
    area["ISO3166-1"="SG"][admin_level=2]->.sg;
    (
      node["shop"](area.sg);
      way["shop"](area.sg);
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

                shops = []
                for element in data.get("elements", []):
                    shop = _parse_osm_element(element)
                    if shop:
                        shops.append(shop)

                print(f"Success: Fetched {len(shops)} records from OpenStreetMap via {endpoint}")
                if shops:
                    return shops

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

    return {
        "name": tags.get("name", "Unknown Shop"),
        "address": tags.get("addr:full") or tags.get("addr:street") or "Unknown Address",
        "lat": lat,
        "lng": lon,
        "source": "osm",
        "shop_type": tags.get("shop", "general"),
        "phone": tags.get("phone"),
        "website": tags.get("website"),
        "opening_hours": tags.get("opening_hours"),
    }
