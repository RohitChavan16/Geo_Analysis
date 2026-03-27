from typing import Dict, List


def calculate_confidence(merged_shop: Dict) -> Dict:
    """
    Calculate confidence score for a merged shop record.
    
    Factors considered:
    - Number of sources (more sources = higher confidence)
    - Data completeness (more fields populated = higher confidence)
    - Data consistency (matching data across sources = higher confidence)
    
    Returns confidence score (0-100) and reasoning.
    """
    
    confidence_signals = []
    
    # Signal 1: Multi-source presence (40% weight)
    sources = merged_shop.get('sources', [])
    num_sources = len(sources)
    source_score = min(100, (num_sources / 3) * 100)  # 3 is max sources
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
    
    # Calculate weighted average
    weights = {
        "multi_source_presence": 0.40,
        "data_completeness": 0.30,
        "coordinate_validity": 0.20,
        "text_field_quality": 0.10,
    }
    
    final_score = 0
    for signal_name, signal_value, _ in confidence_signals:
        final_score += signal_value * weights[signal_name]
    
    # Build reasoning
    reasoning = []
    if num_sources >= 2:
        reasoning.append(f"✓ Present in {num_sources} sources")
    elif num_sources == 1:
        reasoning.append("⚠ Present in only 1 source")
    
    if completeness_score > 80:
        reasoning.append("✓ Complete data")
    elif completeness_score > 50:
        reasoning.append("⚠ Partial data")
    else:
        reasoning.append("✗ Missing key fields")
    
    if coord_score == 100:
        reasoning.append("✓ Valid coordinates")
    else:
        reasoning.append("⚠ Coordinate issues")
    
    return {
        "confidence_score": round(final_score, 2),
        "confidence_level": _get_confidence_level(final_score),
        "reasoning": reasoning,
        "signals": [
            {
                "name": name,
                "score": round(score, 2),
                "detail": detail
            }
            for name, score, detail in confidence_signals
        ]
    }


def calculate_completeness(shop: Dict) -> float:
    """
    Score based on how many important fields are populated.
    Max score: 100 (all fields present)
    """
    
    important_fields = [
        'name',        # Required
        'address',     # Important
        'lat',         # Important
        'lng',         # Important
        'phone',       # Nice to have
        'website',     # Nice to have
        'shop_type',   # Nice to have
    ]
    
    filled = 0
    for field in important_fields:
        if shop.get(field) and shop[field] is not None:
            filled += 1
    
    return (filled / len(important_fields)) * 100


def validate_coordinates(shop: Dict) -> float:
    """
    Validate coordinate format and range for Singapore.
    Singapore coordinates roughly: 1.1°N - 1.5°N, 103.6°E - 104.9°E
    """
    
    lat = shop.get('lat')
    lng = shop.get('lng')
    
    if not lat or not lng:
        return 0  # Missing coordinates
    
    # Check if within Singapore bounds (with buffer)
    if 0.9 < lat < 1.6 and 103.4 < lng < 105.0:
        return 100
    
    # Otherwise location seems off
    return 20


def validate_text_fields(shop: Dict) -> float:
    """
    Validate text field quality (length, not just placeholders).
    """
    
    name = shop.get('name') or ''
    address = shop.get('address') or ''
    name = str(name)
    address = str(address)
    
    score = 0
    
    # Name should be reasonable length
    if len(name.strip()) > 3 and name != "Unknown Shop":
        score += 50
    
    # Address should be reasonable length
    if len(address.strip()) > 10 and address != "Unknown Address":
        score += 50
    
    return score


def _get_confidence_level(score: float) -> str:
    """Convert numeric score to confidence level."""
    
    if score >= 85:
        return "VERY HIGH"
    elif score >= 70:
        return "HIGH"
    elif score >= 50:
        return "MEDIUM"
    elif score >= 30:
        return "LOW"
    else:
        return "VERY LOW"


def enrich_record(shop: Dict, confidence_data: Dict) -> Dict:
    """Add confidence data to shop record."""
    
    return {
        **shop,
        **confidence_data,
        "match_quality": confidence_data.get("confidence_level"),
    }
