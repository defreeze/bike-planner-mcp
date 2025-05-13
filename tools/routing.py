
import random

def get_route_day(start: str, distance_km: int) -> dict:
    # Stubbed response with pseudo-routes
    towns = ["Assen", "Zwolle", "Harderwijk", "Amersfoort", "Utrecht", "Gouda", "Delft", "Leiden", "Haarlem", "Den Haag"]
    next_stop = random.choice(towns)
    return {
        "start": start,
        "end": next_stop,
        "distance": distance_km,
        "waypoints": [start, "Countryside", next_stop]
    }
