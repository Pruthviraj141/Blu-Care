import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth import get_optional_user
from app.facilities.service import FacilitiesService
from app.facilities.schemas import (
    FacilityResult,
    GoogleMapsSearchLinks,
    EmergencyDirectoryResponse,
)
from app.facilities.emergency_contacts import get_emergency_contacts
from app.facilities.maps_urls import build_google_maps_search_url, validate_coordinates

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hospitals", tags=["Facilities & Hospitals"])


class EnhancedNearbyFacilitiesResponse(BaseModel):
    """
    Complete response combining verified real-world healthcare facilities,
    official universal Google Maps search URLs, and status.
    """
    facilities: List[FacilityResult] = Field(default_factory=list)
    external_search: Dict[str, GoogleMapsSearchLinks] = Field(default_factory=dict)
    source: str = "google-maps-scraper"
    status: str = Field("success", description="Search outcome: success, empty, or unavailable")
    message: Optional[str] = None
    latitude: float
    longitude: float
    radius_km: Optional[float] = None
    condition: Optional[str] = None
    providers: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Backward compatibility list for existing UI client"
    )


@router.get("/nearby", response_model=EnhancedNearbyFacilitiesResponse)
async def get_nearby_facilities(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude coordinate"),
    lng: float = Query(..., ge=-180.0, le=180.0, description="Longitude coordinate"),
    radius: Optional[int] = Query(5000, ge=500, le=20000, description="Search radius in meters"),
    radius_km: Optional[float] = Query(None, ge=0.5, le=20.0, description="Search radius in kilometers"),
    limit: int = Query(5, ge=1, le=50, description="Maximum number of facilities to return (default 5)"),
    category: str = Query("all", description="Facility filter: hospital, clinic, doctors, or all"),
    condition: Optional[str] = Query(None, description="Patient condition, symptom or medical specialty context"),
    user_id: str = Depends(get_optional_user),
):
    """
    Discovers nearby verified hospitals, clinics, and doctor practices using
    real-world scraping and generates universal Google Maps search and directions links.
    """
    # Use radius_km if supplied, otherwise fallback to radius (in meters)
    effective_radius_meters = int(radius_km * 1000) if radius_km is not None else (radius or 5000)

    logger.info(
        f"Facility discovery requested by user '{user_id}' at lat={lat}, lng={lng}, "
        f"radius={effective_radius_meters}m (radius_km={radius_km}), category={category}, condition={condition}"
    )

    try:
        validate_coordinates(lat, lng)
        service = FacilitiesService()
        result = await service.search_nearby_async(
            lat=lat,
            lng=lng,
            radius=effective_radius_meters,
            limit=limit,
            category=category,
            condition_name=condition,
        )

        # Convert scraped facilities to backward-compatible provider items for legacy UI clients
        compat_providers = []
        for fac in result.facilities:
            dist_label = fac.distance_formatted or (
                f"{fac.distance_meters / 1000:.1f} km away"
                if fac.distance_meters >= 1000
                else f"{int(fac.distance_meters)} m away"
            )
            compat_providers.append({
                "id": fac.id,
                "name": fac.name or f"Unnamed {fac.category.capitalize()}",
                "type": fac.category.capitalize(),
                "distance": dist_label,
                "eta": "Navigation via Google Maps",
                "phone": fac.phone or "N/A",
                "status": f"Verified ({fac.specialty or fac.emergency or 'General'})",
                "driver": "N/A",
                "vehicleNo": fac.source_url or "Verified Listing",
                "maps_url": fac.maps_url,
                "directions_url": fac.directions_url,
                "rating": fac.rating,
                "address": fac.address,
            })

        return EnhancedNearbyFacilitiesResponse(
            facilities=result.facilities,
            external_search=result.external_search,
            source=result.source,
            status=result.status,
            message=result.message,
            latitude=lat,
            longitude=lng,
            radius_km=effective_radius_meters / 1000.0,
            condition=condition,
            providers=compat_providers,
        )

    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error querying nearby facilities: {e}", exc_info=True)
        # Never crash the API — degrade gracefully with Google Maps search links
        maps_links = GoogleMapsSearchLinks(
            hospitals_url=build_google_maps_search_url(lat, lng, "hospitals"),
            clinics_url=build_google_maps_search_url(lat, lng, "clinics"),
            doctors_url=build_google_maps_search_url(lat, lng, "doctors"),
        )
        return EnhancedNearbyFacilitiesResponse(
            facilities=[],
            external_search={"google_maps": maps_links},
            source="google-maps-scraper",
            status="unavailable",
            message="Live facility scraping temporarily unavailable. Use external Google Maps links.",
            latitude=lat,
            longitude=lng,
            radius_km=effective_radius_meters / 1000.0,
            condition=condition,
            providers=[],
        )


@router.get("/emergency-contacts", response_model=EmergencyDirectoryResponse)
async def get_emergency_contacts_endpoint(
    country: Optional[str] = Query(None, description="Country filter (e.g., India, United States, United Kingdom)"),
    region: Optional[str] = Query(None, description="State or territory filter"),
):
    """
    Returns verified government emergency telephone directory (e.g. India 112 ERSS, US 911, UK 999).
    Does not require or wait on any external map or LLM services.
    """
    return get_emergency_contacts(country=country, region=region)
