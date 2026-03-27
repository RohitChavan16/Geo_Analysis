import os
import time
from typing import Dict, List

import requests

from processors.category_filter import classify_text_category

ONEMAP_API_URL = "https://www.onemap.gov.sg/api/common/elastic"
ONEMAP_TIMEOUT_SECONDS = 15
ONEMAP_MAX_RETRIES = 3
ONEMAP_DEFAULT_QUERIES = [
    "restaurant",
    "cafe",
    "tourist attraction",
    "hotel",
    "amusement park",
    "shopping mall",
    "department store",
    "supermarket",
    "grocery",
    "pharmacy",
    "fuel station",
]


def get_mock_onemap_data() -> List[Dict]:
    """Return mock OneMap challenge-category data for testing/fallback."""
    return [
        {
            "name": "Sample OneMap Restaurant",
            "address": "555 Marina Boulevard, Singapore",
            "lat": 1.2867,
            "lng": 103.8606,
            "shop_type": "restaurant",
            "source": "onemap",
            "postal_code": "018971",
        },
        {
            "name": "Sample OneMap Mall",
            "address": "888 Sentosa Island, Singapore",
            "lat": 1.2496,
            "lng": 103.8263,
            "shop_type": "shopping_mall",
            "source": "onemap",
            "postal_code": "099891",
        },
    ]


def fetch_onemap_shops(
    query: str = "restaurant",
    use_mock: bool = False,
    allow_mock_fallback: bool = False,
) -> List[Dict]:
    """Fetch challenge-category places from OneMap with retry and optional fallback."""

    if use_mock:
        print("Info: Using mock OneMap data")
        return get_mock_onemap_data()

    all_places = []
    seen_keys = set()
    access_token = os.getenv("ONEMAP_ACCESS_TOKEN") or os.getenv("ONEMAP_API_KEY")
    max_pages = int(os.getenv("ONEMAP_MAX_PAGES", "8"))

    queries = ONEMAP_DEFAULT_QUERIES.copy()
    normalized_query = (query or "").strip().lower()
    if normalized_query and normalized_query not in queries:
        queries.insert(0, normalized_query)

    try:
        for current_query in queries:
            page_num = 1
            while page_num <= max_pages:
                params = {
                    "searchVal": current_query,
                    "returnGeom": "Y",
                    "getAddrDetails": "Y",
                    "pageNum": page_num,
                }

                headers = {}
                if access_token:
                    headers["Authorization"] = f"Bearer {access_token}"

                response = None
                for attempt in range(ONEMAP_MAX_RETRIES):
                    response = requests.get(
                        f"{ONEMAP_API_URL.rstrip('/')}/search",
                        params=params,
                        headers=headers,
                        timeout=ONEMAP_TIMEOUT_SECONDS,
                    )

                    if response.status_code in (429, 500, 502, 503, 504):
                        sleep_seconds = 2 ** attempt
                        print(
                            f"Warning: OneMap returned {response.status_code}; retrying in {sleep_seconds}s..."
                        )
                        time.sleep(sleep_seconds)
                        continue

                    if response.status_code in (401, 403) and headers:
                        print("Warning: OneMap auth rejected token. Retrying without token header...")
                        headers = {}
                        time.sleep(1)
                        continue

                    break

                if response is None:
                    raise requests.exceptions.RequestException("No response from OneMap API")

                response.raise_for_status()
                data = response.json()

                results = data.get("results", [])
                if not results:
                    break

                for result in results:
                    place = _parse_onemap_result(result)
                    if not place:
                        continue

                    place_key = _place_dedup_key(place)
                    if place_key in seen_keys:
                        continue
                    seen_keys.add(place_key)
                    all_places.append(place)

                total_pages = int(data.get("totalNumPages", 0) or 0)
                if total_pages and page_num >= total_pages:
                    break

                page_num += 1
                time.sleep(0.6)

            time.sleep(0.5)

        print(f"Success: Fetched {len(all_places)} records from OneMap")
        if all_places:
            return all_places
        return get_mock_onemap_data() if allow_mock_fallback else []

    except requests.exceptions.RequestException as e:
        print(f"Warning: Error fetching OneMap data: {e}")
        return get_mock_onemap_data() if allow_mock_fallback else []
    except Exception as e:
        print(f"Warning: Unexpected error in fetch_onemap_shops: {e}")
        return get_mock_onemap_data() if allow_mock_fallback else []


def _parse_onemap_result(result: Dict) -> Dict:
    """Parse OneMap search result into standardized format and enforce challenge categories."""
    try:
        name = result.get("NAME") or result.get("BUILDING") or "Unknown Place"
        address = result.get("ADDRESS", "Unknown Address")
        category = classify_text_category(name, address)
        if not category:
            return None

        place = {
            "name": name,
            "address": address,
            "lat": float(result.get("LATITUDE", 0)),
            "lng": float(result.get("LONGITUDE", 0)),
            "source": "onemap",
            "shop_type": category,
            "postal_code": result.get("POSTAL", ""),
            "block": result.get("BLK_NO", ""),
            "road": result.get("ROAD_NAME", ""),
        }

        if place["lat"] == 0 or place["lng"] == 0:
            return None

        return place

    except (ValueError, KeyError, TypeError):
        return None


def _place_dedup_key(place: Dict) -> str:
    """Stable key for deduplicating OneMap places from multiple queries."""
    name = str(place.get("name", "")).strip().lower()
    postal = str(place.get("postal_code", "")).strip()
    lat = round(float(place.get("lat", 0) or 0), 6)
    lng = round(float(place.get("lng", 0) or 0), 6)
    return f"{name}|{postal}|{lat}|{lng}"
