import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class FacilityResult(BaseModel):
    """Pydantic model representing a verified scraped healthcare facility."""
    id: str = Field(..., description="Unique facility identifier")
    name: Optional[str] = Field(None, description="Official name of the facility")
    category: str = Field(..., description="Facility category: hospital, clinic, or doctors")
    latitude: float = Field(..., description="Geographic latitude coordinate")
    longitude: float = Field(..., description="Geographic longitude coordinate")
    address: Optional[str] = Field(None, description="Constructed physical address from listing")
    phone: Optional[str] = Field(None, description="Contact phone number if published")
    website: Optional[str] = Field(None, description="Official website URL")
    opening_hours: Optional[str] = Field(None, description="Operating hours if published")
    emergency: Optional[str] = Field("no", description="Emergency services availability (yes/no)")
    specialty: Optional[str] = Field(None, description="Verified medical specialty or facility type")
    rating: Optional[float] = Field(None, description="Rating out of 5.0")
    review_count: Optional[int] = Field(None, description="Total review count")
    distance_meters: float = Field(..., description="Calculated Haversine distance from search center in meters")
    distance_formatted: Optional[str] = Field(None, description="Human readable distance string")
    source_url: Optional[str] = Field(None, description="Original source listing link")
    maps_url: Optional[str] = Field(None, description="Google Maps navigation or search link for the specific facility")
    directions_url: Optional[str] = Field(None, description="Direct turn-by-turn navigation URL")
    source: str = Field(default="scraper", description="Primary data source: scraper")
    # Backwards compatibility fields for legacy clients
    osm_type: Optional[str] = Field("facility", description="Legacy type field")
    osm_id: Optional[int] = Field(0, description="Legacy id field")
    osm_url: Optional[str] = Field(None, description="Legacy URL field")
    retrieved_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        description="Timestamp of retrieval"
    )


class GoogleMapsSearchLinks(BaseModel):
    """Universal Google Maps search URLs for broad local discovery without paid API."""
    hospitals_url: Optional[str] = Field(None, description="Google Maps search link for nearby hospitals")
    clinics_url: Optional[str] = Field(None, description="Google Maps search link for nearby clinics")
    doctors_url: Optional[str] = Field(None, description="Google Maps search link for nearby doctors")


class NearbyFacilitiesResponse(BaseModel):
    """API response contract for nearby healthcare discovery."""
    facilities: List[FacilityResult] = Field(default_factory=list)
    external_search: Dict[str, GoogleMapsSearchLinks] = Field(
        default_factory=dict,
        description="External search links keyed by provider (e.g., google_maps)"
    )
    source: str = "scraper"
    status: str = Field("success", description="Search outcome: success, empty, or unavailable")
    message: Optional[str] = Field(None, description="Human-readable status or diagnostic note")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = None
    condition: Optional[str] = None


class EmergencyContact(BaseModel):
    """Verified emergency contact entry."""
    country: str = Field(..., description="Country name or ISO code")
    region: Optional[str] = Field(None, description="Applicable state, territory, or district")
    number: str = Field(..., description="Emergency telephone number")
    service: str = Field(..., description="Designated emergency service (e.g. Integrated Emergency, Ambulance)")
    official_source: str = Field(..., description="Authoritative government verification URL or authority")
    last_verification_date: str = Field(..., description="Date of last official programmatic check (YYYY-MM)")
    verification_status: str = Field("verified", description="Verification confidence status")
    notes: Optional[str] = Field(None, description="Operational scope or dispatch instructions")


class EmergencyDirectoryResponse(BaseModel):
    """Response returning directory of verified emergency response numbers."""
    contacts: List[EmergencyContact] = Field(default_factory=list)
    disclaimer: str = Field(
        default="Emergency telephone services are managed by respective national/regional government authorities. "
                "BluCare+ provides informational directories and does not dispatch emergency services.",
        description="Legal and medical disclaimer"
    )
