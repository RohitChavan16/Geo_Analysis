import os
import time
from typing import Dict, List

import requests

ONEMAP_API_URL = "https://www.onemap.gov.sg/api/common/elastic"
ONEMAP_TIMEOUT_SECONDS = 15
ONEMAP_MAX_RETRIES = 3


def get_mock_onemap_data() -> List[Dict]:
    """Return mock OneMap shop data for testing/fallback."""
    return [
        {
            "name": "Sample OneMap Shop 1",
            "address": "555 Marina Boulevard, Singapore",
            "lat": 1.2867,
            "lng": 103.8606,
            "phone": "+65 6225 5544",
            "opening_hours": "08:00-20:00",
            "source": "onemap",
            "postal_code": "018971",
        },
        {
            "name": "Sample OneMap Shop 2",
            "address": "888 Sentosa Island, Singapore",
            "lat": 1.2496,
            "lng": 103.8263,
            "phone": "+65 6275 0331",
            "opening_hours": "09:00-23:00",
            "source": "onemap",
            "postal_code": "099891",
        },
    ]


def fetch_onemap_shops(
    query: str = "shop",
    use_mock: bool = False,
    allow_mock_fallback: bool = False,
) -> List[Dict]:
    """Fetch shops from OneMap Singapore API with retry and optional fallback."""

    if use_mock:
        print("Info: Using mock OneMap data")
        return get_mock_onemap_data()

    all_shops = []
    page_num = 1
    access_token = os.getenv("ONEMAP_ACCESS_TOKEN") or os.getenv("ONEMAP_API_KEY")

    try:
        while page_num <= 3:
            params = {
                "searchVal": query,
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

                # Retry on rate-limit or transient gateway/server issues.
                if response.status_code in (429, 500, 502, 503, 504):
                    sleep_seconds = 2 ** attempt
                    print(
                        f"Warning: OneMap returned {response.status_code}; retrying in {sleep_seconds}s..."
                    )
                    time.sleep(sleep_seconds)
                    continue

                # If token fails auth, retry once without token for public endpoint behavior.
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
                shop = _parse_onemap_result(result)
                if shop:
                    all_shops.append(shop)

            total_pages = int(data.get("totalNumPages", 0) or 0)
            if total_pages and page_num >= total_pages:
                break

            page_num += 1
            time.sleep(1.0)

        print(f"Success: Fetched {len(all_shops)} records from OneMap")
        if all_shops:
            return all_shops
        return get_mock_onemap_data() if allow_mock_fallback else []

    except requests.exceptions.RequestException as e:
        print(f"Warning: Error fetching OneMap data: {e}")
        return get_mock_onemap_data() if allow_mock_fallback else []
    except Exception as e:
        print(f"Warning: Unexpected error in fetch_onemap_shops: {e}")
        return get_mock_onemap_data() if allow_mock_fallback else []


def _parse_onemap_result(result: Dict) -> Dict:
    """Parse OneMap search result into standardized format."""
    try:
        shop = {
            "name": result.get("NAME") or result.get("BUILDING") or "Unknown Shop",
            "address": result.get("ADDRESS", "Unknown Address"),
            "lat": float(result.get("LATITUDE", 0)),
            "lng": float(result.get("LONGITUDE", 0)),
            "source": "onemap",
            "postal_code": result.get("POSTAL", ""),
            "block": result.get("BLK_NO", ""),
            "road": result.get("ROAD_NAME", ""),
        }

        if shop["lat"] == 0 or shop["lng"] == 0:
            return None

        return shop

    except (ValueError, KeyError, TypeError):
        return None
