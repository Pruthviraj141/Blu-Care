import logging
from langchain_core.tools import tool
from app.facilities.service import FacilitiesService
from app.facilities.distance import format_distance
from app.facilities.maps_urls import build_google_maps_search_url

logger = logging.getLogger(__name__)


@tool
def find_nearby_facilities(disease: str, facility_type: str, lat: float, lon: float) -> str:
    """
    Finds nearby hospitals, clinics, or doctor practices using scraping-based facility discovery
    and provides verified destination coordinates, turn-by-turn directions, and universal Google Maps search links.
    
    Args:
        disease: The condition the user has (e.g. 'cardiac', 'orthopedic', 'fever', 'emergency').
        facility_type: Category requested ('hospital', 'clinic', 'doctors', or 'all').
        lat: Latitude of the user.
        lon: Longitude of the user.
    
    Returns:
        A formatted string containing nearby verified facilities sorted by actual distance,
        with addresses, phone numbers, and direct navigation links.
    """
    logger.info(f"Facilities tool invoked: lat={lat}, lon={lon}, disease={disease}, facility_type={facility_type}")

    # Map facility_type to allowed category
    norm_type = facility_type.lower().strip() if facility_type else "hospital"
    if "ambulance" in norm_type or "hospital" in norm_type:
        cat = "hospital"
    elif "clinic" in norm_type:
        cat = "clinic"
    elif "doctor" in norm_type:
        cat = "doctors"
    else:
        cat = "all"

    try:
        service = FacilitiesService()
        response = service.search_nearby(
            lat=lat,
            lng=lon,
            radius=5000,
            limit=5,
            category=cat,
            condition_name=disease,
        )
        
        maps_search_url = build_google_maps_search_url(
            lat, lon, "hospitals" if cat == "all" else cat
        )

        output_lines = [
            f"**Nearby Healthcare Facilities (sorted nearest first by actual distance):**\n"
        ]

        if response.facilities:
            for idx, fac in enumerate(response.facilities, 1):
                dist_str = fac.distance_formatted or format_distance(fac.distance_meters)
                name_str = fac.name or f"Unnamed {fac.category.capitalize()}"
                phone_str = f" | Phone: {fac.phone}" if fac.phone else ""
                addr_str = f"\n   - Address: {fac.address}" if fac.address else ""
                nav_link = f"[Turn-by-Turn Directions]({fac.directions_url})" if fac.directions_url else f"[Google Maps]({fac.maps_url})"

                output_lines.append(
                    f"{idx}. **{name_str}** ({fac.category.capitalize()} - ~{dist_str} away{phone_str}){addr_str}\n"
                    f"   - {nav_link}"
                )
        else:
            output_lines.append(f"No healthcare facilities discovered within 5 km.")

        output_lines.append(
            f"\n🔗 **Broader Local Search:** Open [Google Maps Nearby {cat.capitalize()}s]({maps_search_url}) for complete neighborhood directory."
        )

        return "\n".join(output_lines)

    except Exception as e:
        logger.error(f"Error in find_nearby_facilities tool: {e}", exc_info=True)
        try:
            fallback_maps_url = build_google_maps_search_url(lat, lon, "hospitals")
            return (
                f"Could not retrieve local facilities at this moment.\n"
                f"You can search directly on Google Maps: [Find Nearby Hospitals on Google Maps]({fallback_maps_url})"
            )
        except Exception:
            return f"Error retrieving nearby facilities: {str(e)}"
