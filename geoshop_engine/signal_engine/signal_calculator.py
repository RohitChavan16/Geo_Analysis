from typing import Dict, List, Optional

from signal_engine.digital_footprint import calculate_digital_footprint


def calculate_confidence(merged_shop: Dict, source_counts: Optional[Dict] = None) -> Dict:
    """
    Calculate confidence score for a merged shop record.

    Core confidence focuses on record quality. A second score from
    digital footprint signals is then blended into a final decision score.
    """
    confidence_signals = []

    # Signal 1: Multi-source presence (40% weight)
    sources = merged_shop.get("sources", [])
    num_sources = len(sources)
    source_score = min(100, (num_sources / 3) * 100)
    confidence_signals.append(("multi_source_presence", source_score, num_sources))

    # Signal 2: Data completeness (30% weight)
    completeness_score = calculate_completeness(merged_shop)
    confidence_signals.append(("data_completeness", completeness_score, None))

    # Signal 3: Coordinate validity (20% weight)
    coord_score = validate_coordinates(merged_shop)
    confidence_signals.append(("coordinate_validity", coord_score, None))

    # Signal 4: Text field quality (10% weight)
    text_score = validate_text_fields(merged_shop)
    confidence_signals.append(("text_field_quality", text_score, None))

    weights = {
        "multi_source_presence": 0.40,
        "data_completeness": 0.30,
        "coordinate_validity": 0.20,
        "text_field_quality": 0.10,
    }

    confidence_score = 0.0
    for signal_name, signal_value, _ in confidence_signals:
        confidence_score += signal_value * weights[signal_name]

    digital = calculate_digital_footprint(merged_shop, source_counts or {})
    decision_score = (confidence_score * 0.60) + (digital["vitality_score"] * 0.40)

    reasoning = []
    if num_sources >= 2:
        reasoning.append(f"Present in {num_sources} sources")
    elif num_sources == 1:
        reasoning.append("Present in only 1 source")

    if completeness_score > 80:
        reasoning.append("Complete data")
    elif completeness_score > 50:
        reasoning.append("Partial data")
    else:
        reasoning.append("Missing key fields")

    if coord_score == 100:
        reasoning.append("Valid coordinates")
    else:
        reasoning.append("Coordinate issues")

    reasoning.extend(digital["reasons"])

    return {
        "confidence_score": round(confidence_score, 2),
        "confidence_level": _get_confidence_level(confidence_score),
        "decision_score": round(decision_score, 2),
        "decision_level": _get_confidence_level(decision_score),
        "decision_status": digital["status"],
        "digital_footprint_score": round(digital["vitality_score"], 2),
        "digital_signals": digital["signals"],
        "reasoning": reasoning,
        "signals": [
            {"name": name, "score": round(score, 2), "detail": detail}
            for name, score, detail in confidence_signals
        ],
    }


def calculate_completeness(shop: Dict) -> float:
    important_fields = [
        "name",
        "address",
        "lat",
        "lng",
        "phone",
        "website",
        "shop_type",
    ]

    filled = 0
    for field in important_fields:
        if shop.get(field) is not None and str(shop.get(field)).strip() != "":
            filled += 1

    return (filled / len(important_fields)) * 100


def validate_coordinates(shop: Dict) -> float:
    # Singapore bounds with slight buffer.
    lat = shop.get("lat")
    lng = shop.get("lng")

    if lat is None or lng is None:
        return 0

    if 0.9 < lat < 1.6 and 103.4 < lng < 105.0:
        return 100

    return 20


def validate_text_fields(shop: Dict) -> float:
    name = str(shop.get("name") or "")
    address = str(shop.get("address") or "")

    score = 0
    if len(name.strip()) > 3 and name != "Unknown Shop":
        score += 50

    if len(address.strip()) > 10 and address != "Unknown Address":
        score += 50

    return float(score)


def _get_confidence_level(score: float) -> str:
    if score >= 85:
        return "VERY HIGH"
    if score >= 70:
        return "HIGH"
    if score >= 50:
        return "MEDIUM"
    if score >= 30:
        return "LOW"
    return "VERY LOW"


def enrich_record(shop: Dict, confidence_data: Dict) -> Dict:
    return {**shop, **confidence_data, "match_quality": confidence_data.get("decision_level")}
