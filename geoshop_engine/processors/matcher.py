from typing import List, Dict
from difflib import SequenceMatcher
import math
import re


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two coordinates in kilometers (Haversine formula)."""
    
    R = 6371  # Earth's radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def _normalize_text(value: str) -> str:
    """Normalize business/address text for fuzzy comparison."""
    text = str(value or "").lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_postal_code(value: str) -> str:
    """Extract Singapore postal code when present."""
    text = str(value or "")
    match = re.search(r"\b(\d{6})\b", text)
    return match.group(1) if match else ""


def string_similarity(str1: str, str2: str) -> float:
    """Calculate normalized string similarity score (0-1)."""
    
    if not str1 or not str2:
        return 0.0
    
    # Normalize strings and guard against non-string values.
    s1 = _normalize_text(str1)
    s2 = _normalize_text(str2)
    
    # Exact match
    if s1 == s2:
        return 1.0
    
    # Use SequenceMatcher for similarity ratio
    matcher = SequenceMatcher(None, s1, s2)
    ratio = matcher.ratio()

    # Token-order-insensitive ratio to handle "Starbucks Orchard" vs "Orchard Starbucks".
    tokens1 = " ".join(sorted(s1.split()))
    tokens2 = " ".join(sorted(s2.split()))
    token_ratio = SequenceMatcher(None, tokens1, tokens2).ratio()

    return max(ratio, token_ratio)


def match_shops(all_shops: List[Dict], distance_threshold: float = 0.05) -> List[List[Dict]]:
    """
    Match shops across multiple data sources.
    Returns list of groups where each group contains matching shops.
    
    Args:
        all_shops: List of shop records from all sources
        distance_threshold: Max distance in km to consider shops as same (default 100m)
    
    Returns:
        List of shop groups (each group = matched shops across sources)
    """
    
    matched = []
    used_indices = set()
    
    for i, shop in enumerate(all_shops):
        if i in used_indices:
            continue
        
        # Start a new group with this shop
        group = [shop]
        used_indices.add(i)
        
        # Find matches for this shop in remaining shops
        for j in range(i + 1, len(all_shops)):
            if j in used_indices:
                continue
            
            if shops_match(shop, all_shops[j], distance_threshold):
                group.append(all_shops[j])
                used_indices.add(j)
        
        matched.append(group)
    
    return matched


def shops_match(shop1: Dict, shop2: Dict, distance_threshold: float = 0.05) -> bool:
    """
    Determine if two shops are the same based on name, address, and location.
    
    Returns True if shops are likely duplicates.
    """
    
    # Don't match shops from same source
    if shop1.get('source') == shop2.get('source'):
        return False
    
    # Check location distance first (most important for same physical entity).
    try:
        lat1, lng1 = shop1['lat'], shop1['lng']
        lat2, lng2 = shop2['lat'], shop2['lng']
        distance = calculate_distance(lat1, lng1, lat2, lng2)
    except (KeyError, TypeError):
        return False

    # Spatial gate: if too far, it's not the same shop.
    if distance > distance_threshold:
        return False

    # Fuzzy text signals.
    name_sim = string_similarity(shop1.get('name', ''), shop2.get('name', ''))
    addr_sim = string_similarity(shop1.get('address', ''), shop2.get('address', ''))
    postal1 = shop1.get('postal_code') or _extract_postal_code(shop1.get('address', ''))
    postal2 = shop2.get('postal_code') or _extract_postal_code(shop2.get('address', ''))

    # Strong rule: very close + decent fuzzy name.
    if distance < 0.05 and name_sim >= 0.70:
        return True

    # Strong alternative: very close + strong address.
    if distance < 0.05 and addr_sim >= 0.80:
        return True

    # Postal code agreement is a strong tie-breaker.
    if postal1 and postal2 and postal1 == postal2 and distance < 0.10 and name_sim >= 0.55:
        return True

    # Strict fallback for almost identical coordinates.
    if distance < 0.02 and (name_sim >= 0.60 or addr_sim >= 0.70):
        return True

    return False


def merge_shop_groups(shop_group: List[Dict]) -> Dict:
    """
    Merge a group of matched shops into one record (data from all sources).
    Prioritizes non-null values and picks best data.
    """
    
    merged = {
        "name": None,
        "address": None,
        "lat": None,
        "lng": None,
        "sources": [],
        "phone": None,
        "website": None,
        "opening_hours": None,
        "shop_type": None,
        "all_records": shop_group,
    }
    
    # Collect all sources
    merged['sources'] = list(set(s.get('source', 'unknown') for s in shop_group))
    
    # Pick name: prefer longer names (likely more complete)
    names = [s.get('name') for s in shop_group if s.get('name')]
    if names:
        merged['name'] = max(names, key=len)
    
    # Pick address: prefer longer addresses
    addresses = [s.get('address') for s in shop_group if s.get('address')]
    if addresses:
        merged['address'] = max(addresses, key=len)
    
    # Average coordinates
    lats = [s['lat'] for s in shop_group if 'lat' in s and s['lat']]
    lngs = [s['lng'] for s in shop_group if 'lng' in s and s['lng']]
    if lats:
        merged['lat'] = sum(lats) / len(lats)
    if lngs:
        merged['lng'] = sum(lngs) / len(lngs)
    
    # Pick best contact info (any non-null value)
    for field in ['phone', 'website', 'opening_hours', 'shop_type']:
        for shop in shop_group:
            if shop.get(field):
                merged[field] = shop.get(field)
                break
    
    return merged
