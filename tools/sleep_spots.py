
def suggest_sleep_spot(location: str) -> dict:
    return {
        "location": location,
        "type": "campground",
        "name": f"Camping {location}",
        "price_eur": 15,
        "has_showers": True
    }
