from processors.category_filter import classify_text_category


def normalize_datagov(records):
    clean = []

    for r in records:
        # Handle mixed key styles across datasets.
        name = r.get("name") or r.get("Name") or r.get("business_name") or r.get("BusinessName")
        address = r.get("address") or r.get("Address")
        lat = r.get("latitude") or r.get("Latitude") or r.get("lat") or r.get("LATITUDE")
        lng = r.get("longitude") or r.get("Longitude") or r.get("lng") or r.get("LONGITUDE")

        try:
            lat = float(lat) if lat is not None else None
            lng = float(lng) if lng is not None else None
        except (TypeError, ValueError):
            lat, lng = None, None

        if lat is None or lng is None:
            continue

        category = classify_text_category(name, address)
        if not category:
            continue

        place = {
            "name": name or "Unknown Shop",
            "address": address or "Unknown Address",
            "lat": lat,
            "lng": lng,
            "shop_type": category,
            "postal_code": r.get("postal_code") or r.get("PostalCode") or r.get("POSTAL"),
            "source": "data_gov"
        }

        clean.append(place)

    return clean
