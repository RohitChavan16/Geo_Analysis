from typing import Dict, List


def _source_reliability(source_name: str, source_counts: Dict) -> float:
    base = {
        "data_gov": 1.00,
        "datagov": 1.00,
        "onemap": 0.85,
        "osm": 0.70,
        "chope": 0.75,
        "burpple": 0.70,
        "deliveroo": 0.75,
        "whyq": 0.75,
        "sfa": 0.95,
        "ura": 0.80,
        "sha": 0.85,
    }.get(source_name, 0.60)

    count = (
        source_counts.get(source_name)
        or source_counts.get("data_gov" if source_name == "datagov" else source_name)
        or 0
    )
    if count < 10:
        return base * 0.50
    if count < 50:
        return base * 0.75
    return base


def _contains_any(value: str, tokens: List[str]) -> bool:
    text = str(value or "").lower()
    return any(token in text for token in tokens)


def calculate_digital_footprint(merged_shop: Dict, source_counts: Dict) -> Dict:
    """
    Compute digital-footprint vitality score (0-100) for open/closed decisioning.
    Uses only non-Google-compatible signals.
    """
    sources = list(set(merged_shop.get("sources", [])))
    name = str(merged_shop.get("name") or "")
    website = str(merged_shop.get("website") or "")
    opening_hours = str(merged_shop.get("opening_hours") or "")
    phone = str(merged_shop.get("phone") or "")
    category = str(merged_shop.get("shop_type") or "")

    reliability = [_source_reliability(source, source_counts) for source in sources]
    avg_reliability = (sum(reliability) / len(reliability)) if reliability else 0.50

    score = 0.0
    reasons: List[str] = []
    signals = []

    official_signal = 0.0
    if "data_gov" in sources or "datagov" in sources:
        official_signal += 32.0
    if "sfa" in sources:
        official_signal += 8.0
    score += official_signal
    signals.append({"name": "official_presence", "score": round(official_signal, 2)})
    if official_signal > 0:
        reasons.append("Found in official/public registry sources")
    else:
        reasons.append("No official registry signal in this run")

    map_signal = 0.0
    if "onemap" in sources:
        map_signal += 15.0
    if "osm" in sources:
        map_signal += 10.0
    score += map_signal
    signals.append({"name": "map_presence", "score": round(map_signal, 2)})

    activity_signal = 0.0
    if phone.strip():
        activity_signal += 5.0
    if website.strip():
        activity_signal += 8.0
    if opening_hours.strip():
        activity_signal += 7.0
    score += activity_signal
    signals.append({"name": "contact_activity_fields", "score": round(activity_signal, 2)})
    if activity_signal > 0:
        reasons.append("Has live contact/activity fields")

    vertical_signal = 0.0
    if _contains_any(website, ["chope", "deliveroo", "whyq", "foodpanda", "booking.com"]):
        vertical_signal += 8.0
    if _contains_any(name, ["mall", "hotel", "station", "pharmacy", "restaurant", "cafe"]):
        vertical_signal += 3.0
    if category in {"restaurant", "cafe", "hotel", "fuel_station", "pharmacy"}:
        vertical_signal += 4.0
    score += vertical_signal
    signals.append({"name": "vertical_platform_signal", "score": round(vertical_signal, 2)})

    source_diversity = min(15.0, len(sources) * 5.0)
    score += source_diversity
    signals.append({"name": "source_diversity", "score": round(source_diversity, 2)})

    score *= avg_reliability
    signals.append({"name": "reliability_factor", "score": round(avg_reliability * 100.0, 2)})

    score = max(0.0, min(100.0, score))

    if score >= 70:
        status = "ACTIVE"
    elif score >= 30:
        status = "UNCERTAIN"
    else:
        status = "LIKELY_CLOSED"

    return {
        "vitality_score": round(score, 2),
        "status": status,
        "signals": signals,
        "reasons": reasons,
    }
