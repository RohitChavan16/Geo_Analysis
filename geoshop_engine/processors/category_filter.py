from typing import Dict, Optional


ALLOWED_CATEGORIES = {
    "restaurant",
    "cafe",
    "tourist_attraction",
    "hotel",
    "amusement_park",
    "shopping_mall",
    "department_store",
    "grocery_store",
    "pharmacy",
    "fuel_station",
}


def map_osm_category(tags: Dict) -> Optional[str]:
    """Map OSM tags to challenge categories."""
    amenity = str(tags.get("amenity", "")).lower()
    tourism = str(tags.get("tourism", "")).lower()
    leisure = str(tags.get("leisure", "")).lower()
    shop = str(tags.get("shop", "")).lower()

    if amenity == "restaurant":
        return "restaurant"
    if amenity == "cafe":
        return "cafe"
    if amenity == "pharmacy":
        return "pharmacy"
    if amenity == "fuel":
        return "fuel_station"

    if tourism == "attraction":
        return "tourist_attraction"
    if tourism == "hotel":
        return "hotel"

    if leisure == "amusement_park":
        return "amusement_park"

    if shop == "mall":
        return "shopping_mall"
    if shop == "department_store":
        return "department_store"
    if shop in ("supermarket", "convenience"):
        return "grocery_store"

    return None


def classify_text_category(name: str, address: str = "") -> Optional[str]:
    """Infer challenge categories from text-only sources (OneMap/data.gov)."""
    text = f"{name or ''} {address or ''}".lower()

    if any(k in text for k in ["restaurant", "diner", "eatery", "bistro"]):
        return "restaurant"
    if any(k in text for k in ["cafe", "coffee"]):
        return "cafe"
    if any(k in text for k in ["attraction", "museum", "zoo", "aquarium", "park"]):
        return "tourist_attraction"
    if any(k in text for k in ["hotel", "resort", "hostel"]):
        return "hotel"
    if any(k in text for k in ["amusement park", "theme park"]):
        return "amusement_park"
    if any(k in text for k in ["mall", "shopping centre", "shopping center"]):
        return "shopping_mall"
    if "department store" in text:
        return "department_store"
    if any(k in text for k in ["supermarket", "grocery", "mart", "minimart", "convenience store"]):
        return "grocery_store"
    if any(k in text for k in ["pharmacy", "drugstore", "chemist"]):
        return "pharmacy"
    if any(k in text for k in ["fuel", "petrol", "gas station", "service station"]):
        return "fuel_station"

    return None
