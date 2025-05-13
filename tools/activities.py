
def find_activities(location: str, preferences: list) -> dict:
    example_activities = {
        "nature": ["bike through a national park", "visit a botanical garden"],
        "historic towns": ["tour a local castle", "walk old town center"],
        "no big cities": ["ride through local villages"]
    }
    activities = []
    for pref in preferences:
        activities.extend(example_activities.get(pref, []))
    return {
        "location": location,
        "recommended": activities[:3]
    }
