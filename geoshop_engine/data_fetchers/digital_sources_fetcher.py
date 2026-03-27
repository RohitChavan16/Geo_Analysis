import json
import os
import re
from typing import Dict, List

import requests

from processors.category_filter import classify_text_category

REQUEST_TIMEOUT_SECONDS = 20


def fetch_digital_sources() -> List[Dict]:
    """
    Optional digital-source ingestion for Singapore footprint signals.
    Disabled by default to avoid unstable scraping in normal runs.
    """
    enabled = os.getenv("DIGITAL_SOURCE_FETCH_ENABLED", "false").lower() == "true"
    if not enabled:
        return []

    records: List[Dict] = []

    local_snapshot_path = os.getenv("DIGITAL_SOURCE_SNAPSHOT_PATH", "").strip()
    if local_snapshot_path:
        records.extend(_read_local_snapshot(local_snapshot_path))

    # Optional HTML listing pages that expose LocalBusiness json-ld blocks.
    for source_name, env_key in [
        ("chope", "CHOPE_LISTING_URL"),
        ("burpple", "BURPPLE_LISTING_URL"),
        ("whyq", "WHYQ_LISTING_URL"),
        ("sha", "SHA_LISTING_URL"),
        ("mall_directory", "MALL_DIRECTORY_URL"),
    ]:
        url = os.getenv(env_key, "").strip()
        if not url:
            continue
        records.extend(_fetch_json_ld_places(url, source_name))

    dedup = {}
    for rec in records:
        key = _dedup_key(rec)
        dedup[key] = rec
    return list(dedup.values())


def _read_local_snapshot(path: str) -> List[Dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as e:
        print(f"Warning: Unable to load digital source snapshot {path}: {e}")
        return []

    if not isinstance(payload, list):
        return []

    records = []
    for item in payload:
        normalized = _normalize_record(item, item.get("source", "snapshot"))
        if normalized:
            records.append(normalized)
    return records


def _fetch_json_ld_places(url: str, source_name: str) -> List[Dict]:
    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers={"User-Agent": "GeoShopEngine/1.0 (Singapore place-change analysis)"},
        )
        response.raise_for_status()
    except Exception as e:
        print(f"Warning: Failed to fetch digital listing ({source_name}) from {url}: {e}")
        return []

    html = response.text
    matches = re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    records: List[Dict] = []
    for match in matches:
        try:
            parsed = json.loads(match.strip())
        except Exception:
            continue
        records.extend(_extract_json_ld_places(parsed, source_name))
    return records


def _extract_json_ld_places(data: Dict, source_name: str) -> List[Dict]:
    places = []
    queue = data if isinstance(data, list) else [data]

    for item in queue:
        if not isinstance(item, dict):
            continue
        item_type = str(item.get("@type", "")).lower()
        if item_type and "localbusiness" not in item_type and "restaurant" not in item_type and "hotel" not in item_type:
            continue

        normalized = _normalize_record(item, source_name)
        if normalized:
            places.append(normalized)
    return places


def _normalize_record(item: Dict, source_name: str) -> Dict:
    name = item.get("name") or item.get("title")
    address = item.get("address")
    if isinstance(address, dict):
        address = ", ".join(
            [
                str(address.get("streetAddress", "")),
                str(address.get("postalCode", "")),
                str(address.get("addressLocality", "")),
                str(address.get("addressCountry", "")),
            ]
        )
    lat = None
    lng = None
    geo = item.get("geo", {})
    if isinstance(geo, dict):
        lat = geo.get("latitude")
        lng = geo.get("longitude")
    lat = lat if lat is not None else item.get("lat")
    lng = lng if lng is not None else item.get("lng")

    try:
        lat = float(lat)
        lng = float(lng)
    except Exception:
        return None

    category = classify_text_category(name, address)
    if not category:
        return None

    return {
        "name": name or "Unknown Place",
        "address": address or "Unknown Address",
        "lat": lat,
        "lng": lng,
        "source": source_name,
        "shop_type": category,
        "phone": item.get("telephone") or item.get("phone"),
        "website": item.get("url") or item.get("website"),
        "opening_hours": item.get("openingHours") or item.get("opening_hours"),
        "postal_code": item.get("postalCode") or item.get("postal_code"),
    }


def _dedup_key(rec: Dict) -> str:
    name = str(rec.get("name", "")).strip().lower()
    lat = round(float(rec.get("lat", 0) or 0), 5)
    lng = round(float(rec.get("lng", 0) or 0), 5)
    return f"{name}|{lat}|{lng}"
