import os
import time
from typing import Dict, List

import requests

BASE_URL = "https://data.gov.sg/api/action/datastore_search"
REQUEST_TIMEOUT_SECONDS = 15
MAX_RETRIES = 5
BASE_DELAY_SECONDS = 2.0
DEFAULT_COLLECTION_ID = 2
DEFAULT_MAX_RECORDS = 1000
DATA_GOV_CACHE_TTL_SECONDS = 3600
_DATAGOV_CACHE: Dict[str, Dict] = {}


def get_mock_datagov_data() -> List[Dict]:
    """Return mock data.gov.sg shop data for testing/fallback."""
    return [
        {
            "Name": "Sample Shop 1",
            "Address": "123 Orchard Road, Singapore",
            "Latitude": 1.3034,
            "Longitude": 103.8320,
            "Phone": "+65 1234 5678",
            "Website": "http://example.com/shop1",
            "source": "datagov",
        },
        {
            "Name": "Sample Shop 2",
            "Address": "456 Bugis Street, Singapore",
            "Latitude": 1.3045,
            "Longitude": 103.8565,
            "Phone": "+65 9876 5432",
            "Website": "http://example.com/shop2",
            "source": "datagov",
        },
    ]


def get_resource_id(collection_id: int):
    """Get resource ID from collection metadata."""
    try:
        url = f"https://api-production.data.gov.sg/v2/public/api/collections/{collection_id}/metadata"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "data" not in data or "collectionMetadata" not in data["data"]:
            print(f"Warning: Unexpected API response structure for collection {collection_id}")
            return None

        child_datasets = data["data"]["collectionMetadata"].get("childDatasets", [])
        if not child_datasets:
            print(f"Warning: No child datasets found for collection {collection_id}")
            return None

        return child_datasets[0]
    except Exception as e:
        print(f"Warning: Error getting data.gov.sg resource ID: {e}")
        return None


def fetch_datagov_data(
    collection_id=None,
    use_mock: bool = False,
    max_records: int = DEFAULT_MAX_RECORDS,
    allow_mock_fallback: bool = False,
    force_refresh: bool = False,
):
    """Fetch data from data.gov.sg datastore with retry/backoff and record cap."""

    if use_mock:
        print("Info: Using mock data.gov.sg data")
        return get_mock_datagov_data()

    if not collection_id:
        collection_id = os.getenv("DATA_GOV_COLLECTION_ID", str(DEFAULT_COLLECTION_ID))
        try:
            collection_id = int(collection_id)
        except (TypeError, ValueError):
            collection_id = DEFAULT_COLLECTION_ID

    cache_key = f"{collection_id}:{max_records}"
    now = time.time()
    cache_ttl = int(os.getenv("DATA_GOV_CACHE_TTL_SECONDS", DATA_GOV_CACHE_TTL_SECONDS))
    cache_entry = _DATAGOV_CACHE.get(cache_key)
    if (not force_refresh) and cache_entry and (now - cache_entry["at"] < cache_ttl):
        print(f"Info: Returning cached data.gov.sg records for key={cache_key}")
        return cache_entry["data"]

    try:
        resource_id = get_resource_id(collection_id)
        if not resource_id:
            print(f"Warning: Could not get resource ID for collection {collection_id}")
            return get_mock_datagov_data() if allow_mock_fallback else []

        all_data: List[Dict] = []
        offset = 0
        limit = 100

        while offset < max_records:
            params = {
                "resource_id": resource_id,
                "limit": limit,
                "offset": offset,
            }

            try:
                response = None
                for attempt in range(MAX_RETRIES):
                    response = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)

                    if response.status_code in (429, 500, 502, 503, 504):
                        retry_after = response.headers.get("Retry-After")
                        if retry_after and retry_after.isdigit():
                            sleep_time = float(retry_after)
                        else:
                            sleep_time = BASE_DELAY_SECONDS * (2 ** attempt)
                        print(
                            f"Warning: data.gov.sg returned {response.status_code} at offset {offset}. "
                            f"Retrying in {sleep_time:.1f}s..."
                        )
                        time.sleep(sleep_time)
                        continue

                    break

                if response is None:
                    raise requests.exceptions.RequestException("No response from data.gov.sg")

                response.raise_for_status()
                data = response.json()

                if "result" not in data or "records" not in data["result"]:
                    print("Warning: Unexpected datastore response structure")
                    break

                records = data["result"]["records"]
                if not records:
                    break

                all_data.extend(records)
                offset += limit

                if len(all_data) >= max_records:
                    all_data = all_data[:max_records]
                    print(f"Info: Reached max_records cap ({max_records})")
                    break

                if len(records) < limit:
                    break

                time.sleep(1.0)

            except requests.exceptions.RequestException as e:
                print(f"Warning: Error fetching data.gov.sg: {e}")
                if not all_data:
                    return get_mock_datagov_data() if allow_mock_fallback else []
                break

        print(f"Success: Fetched {len(all_data)} records from data.gov.sg")
        if all_data:
            _DATAGOV_CACHE[cache_key] = {"at": now, "data": all_data}
            return all_data
        return get_mock_datagov_data() if allow_mock_fallback else []

    except Exception as e:
        print(f"Warning: Unexpected error in fetch_datagov_data: {e}")
        return get_mock_datagov_data() if allow_mock_fallback else []
