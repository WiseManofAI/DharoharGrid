"""
spatial_math.py
Standalone spatial math utilities for a heritage app's geofencing engine.

Contains:
- calculate_haversine_distance: great-circle distance between two GPS points
- is_within_geofence: checks if a user is inside a circular radius around a node
"""

import math


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two GPS coordinates
    using the Haversine formula.

    Args:
        lat1, lon1: Latitude and longitude of point 1 (in decimal degrees).
        lat2, lon2: Latitude and longitude of point 2 (in decimal degrees).

    Returns:
        Distance between the two points in kilometers.
    """
    # Earth's mean radius in kilometers
    EARTH_RADIUS_KM = 6371.0

    # Convert all degree values to radians, since Python's math functions
    # (sin, cos) expect radians, not degrees.
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Differences between the two points
    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    # Haversine formula
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance_km = EARTH_RADIUS_KM * c
    return distance_km


def is_within_geofence(user_lat: float, user_lon: float,
                        node_lat: float, node_lon: float,
                        radius_km: float) -> bool:
    """
    Check whether a user's GPS position falls within a circular geofence
    centered on a cultural node.

    Args:
        user_lat, user_lon: The user's current GPS coordinates.
        node_lat, node_lon: The GPS coordinates of the cultural node (geofence center).
        radius_km: The radius of the geofence, in kilometers.

    Returns:
        True if the user is inside (or exactly on) the radius, False otherwise.
    """
    distance = calculate_haversine_distance(user_lat, user_lon, node_lat, node_lon)
    return distance <= radius_km


# --- TEST BLOCK ---
if __name__ == '__main__':
    # Sample coordinates:
    # Jaipur city center (roughly the Hawa Mahal area)
    jaipur_lat, jaipur_lon = 26.9239, 75.8267

    # Bagru town (site of the block printing heritage node)
    bagru_lat, bagru_lon = 26.8398, 75.5427

    # --- Test 1: Raw distance calculation ---
    distance = calculate_haversine_distance(jaipur_lat, jaipur_lon, bagru_lat, bagru_lon)
    print(f"Distance from Jaipur city center to Bagru: {distance:.2f} km")

    # --- Test 2: Geofence check with a radius that should be TOO SMALL ---
    small_radius_km = 5.0
    result_small = is_within_geofence(jaipur_lat, jaipur_lon, bagru_lat, bagru_lon, small_radius_km)
    print(f"Is user within {small_radius_km} km geofence? {result_small}  (expected: False)")

    # --- Test 3: Geofence check with a radius that should COVER the distance ---
    large_radius_km = 40.0
    result_large = is_within_geofence(jaipur_lat, jaipur_lon, bagru_lat, bagru_lon, large_radius_km)
    print(f"Is user within {large_radius_km} km geofence? {result_large}  (expected: True)")

    # --- Test 4: Zero distance (same point) should always be inside any radius ---
    result_same_point = is_within_geofence(jaipur_lat, jaipur_lon, jaipur_lat, jaipur_lon, 0.1)
    print(f"Is user within geofence of their own exact location? {result_same_point}  (expected: True)")