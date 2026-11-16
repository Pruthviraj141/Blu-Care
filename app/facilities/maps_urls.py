import urllib.parse
from typing import Optional

ALLOWED_CATEGORIES = {
    "hospitals": "hospitals",
    "hospital": "hospitals",
    "clinics": "clinics",
    "clinic": "clinics",
    "doctors": "doctors",
    "doctor": "doctors",
}


def validate_coordinates(latitude: float, longitude: float) -> None:
    if not isinstance(latitude, (int, float)) or not (-90.0 <= latitude <= 90.0):
        raise ValueError(f"Invalid latitude: {latitude}. Must be between -90 and 90.")
    if not isinstance(longitude, (int, float)) or not (-180.0 <= longitude <= 180.0):
        raise ValueError(f"Invalid longitude: {longitude}. Must be between -180 and 180.")


def build_google_maps_search_url(
    latitude: float,
    longitude: float,
    category: str = "hospitals",
) -> str:
    """
    Constructs an official, universal Google Maps Search URL without requiring an API key.
    
    Format: https://www.google.com/maps/search/?api=1&query=hospitals+near+LAT%2CLNG
    
    Strict Privacy Rule:
    Zero patient symptoms, medical histories, user identifiers, or diagnostics are ever included.
    """
    validate_coordinates(latitude, longitude)

    normalized_cat = category.strip().lower()
    if normalized_cat not in ALLOWED_CATEGORIES:
        raise ValueError(
            f"Invalid category '{category}'. Allowed categories: {list(set(ALLOWED_CATEGORIES.values()))}"
        )

    cat_name = ALLOWED_CATEGORIES[normalized_cat]
    query = f"{cat_name} near {latitude},{longitude}"

    params = {
        "api": "1",
        "query": query,
    }
    encoded = urllib.parse.urlencode(params)
    return f"https://www.google.com/maps/search/?{encoded}"


def build_google_maps_facility_url(
    name: Optional[str],
    latitude: float,
    longitude: float,
) -> str:
    """Constructs a Google Maps search URL targeted directly to a specific verified facility."""
    validate_coordinates(latitude, longitude)

    if name and name.strip():
        # Sanitize name to avoid unexpected delimiters
        clean_name = " ".join(name.strip().split())
        query = f"{clean_name} {latitude},{longitude}"
    else:
        query = f"{latitude},{longitude}"

    params = {
        "api": "1",
        "query": query,
    }
    encoded = urllib.parse.urlencode(params)
    return f"https://www.google.com/maps/search/?{encoded}"


def build_google_maps_directions_url(latitude: float, longitude: float) -> str:
    """Constructs an official Google Maps navigation / directions URL to the given destination."""
    validate_coordinates(latitude, longitude)
    params = {
        "api": "1",
        "destination": f"{latitude},{longitude}",
    }
    encoded = urllib.parse.urlencode(params)
    return f"https://www.google.com/maps/dir/?{encoded}"


def build_osm_url(osm_type: str, osm_id: int) -> str:
    """Constructs the canonical OpenStreetMap entity link."""
    clean_type = osm_type.strip().lower()
    if clean_type not in ("node", "way", "relation"):
        clean_type = "node"
    return f"https://www.openstreetmap.org/{clean_type}/{osm_id}"
