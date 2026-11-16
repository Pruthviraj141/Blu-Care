"""
Facilities Service for BluCare+ — Real Scraping-Based Facility Discovery.

Orchestrates real-world healthcare facility discovery using headless browser
automation and public directory scraping. Completely replaces OpenStreetMap/Overpass.

Key Principles:
1. Exact Latitude & Longitude Foundation: Search centers strictly around validated GPS coordinates.
2. Verified Coordinates & Haversine Distance: Every facility has verified destination coordinates
   and exact straight-line distance computed from the user's location.
3. Nearest First Ranking: Results are strictly sorted by actual distance (nearest first).
4. Disease-Aware Facility Discovery: Conditions (Cardiac, Orthopedic, Fever, Emergency) guide
   targeted queries and clinical verification without corrupting distance ranking.
5. Deduplication & Radius Expansion: Deduplicates proximate facilities and expands radius when needed.
"""

import asyncio
import hashlib
import logging
from typing import Optional, List, Dict, Any

from app.facilities.schemas import (
    NearbyFacilitiesResponse,
    GoogleMapsSearchLinks,
    FacilityResult,
)
from app.facilities.maps_urls import (
    build_google_maps_search_url,
    build_google_maps_facility_url,
    build_google_maps_directions_url,
    validate_coordinates,
)
from app.facilities.distance import haversine_distance, format_distance
from app.facilities.scraper import HospitalScraper
from app.facilities.specialty_mapper import (
    map_condition_to_facility_query,
    verify_facility_specialty,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class FacilitiesService:
    """
    Coordinates genuine facility discovery using real browser/directory scraping.
    Provides verified destination coordinates, turn-by-turn directions, and disease-aware matching.
    """

    def __init__(self, scraper: Optional[HospitalScraper] = None, client: Optional[Any] = None):
        # Support optional injected scraper (or legacy client param for mock tests)
        self.scraper = scraper or HospitalScraper()
        self._mock_client = client

    @staticmethod
    def _build_external_search_links(lat: float, lng: float) -> GoogleMapsSearchLinks:
        """Constructs Google Maps search links centered on user's exact coordinates."""
        return GoogleMapsSearchLinks(
            hospitals_url=build_google_maps_search_url(lat, lng, "hospitals"),
            clinics_url=build_google_maps_search_url(lat, lng, "clinics"),
            doctors_url=build_google_maps_search_url(lat, lng, "doctors"),
        )

    def _normalize_category(self, facility_type: str, requested_category: str) -> str:
        """Categorizes facility type into standard hospital, clinic, or doctors."""
        ft = (facility_type or "").lower()
        if "hospital" in ft or "medical center" in ft or "trauma" in ft:
            return "hospital"
        if "doctor" in ft or "surgeon" in ft or "physician" in ft or "practitioner" in ft:
            return "doctors"
        if "clinic" in ft or "dispensary" in ft or "health center" in ft:
            return "clinic"
        if requested_category in ("hospital", "clinic", "doctors"):
            return requested_category
        return "hospital"

    def _generate_facility_id(self, name: str, lat: float, lng: float) -> str:
        """Generates a stable unique ID for a facility based on its name and coordinates."""
        raw = f"{name.strip().lower()}:{round(lat, 4)}:{round(lng, 4)}"
        return f"fac-{hashlib.md5(raw.encode()).hexdigest()[:10]}"

    def _process_scraped_records(
        self,
        raw_records: List[Dict[str, Any]],
        user_lat: float,
        user_lng: float,
        radius_meters: int,
        limit: int,
        category: str,
        specialty_info: Dict[str, Any],
    ) -> List[FacilityResult]:
        """
        Validates coordinates, computes Haversine distances, verifies specialties,
        deduplicates, and sorts strictly by distance.
        """
        processed: List[FacilityResult] = []
        seen_coordinates = []

        for rec in raw_records:
            f_lat = rec.get("latitude")
            f_lng = rec.get("longitude")
            f_name = rec.get("name") or "Healthcare Facility"

            if f_lat is None or f_lng is None:
                continue

            try:
                validate_coordinates(f_lat, f_lng)
            except ValueError:
                continue

            # Calculate actual Haversine distance from user coordinates
            dist_meters = haversine_distance(user_lat, user_lng, f_lat, f_lng)

            # Strict radius boundary check: only include facilities within requested radius
            if dist_meters > radius_meters:
                continue

            # Deduplication: check if another facility is within 40m with similar name
            is_dup = False
            for seen_lat, seen_lng, seen_name in seen_coordinates:
                if haversine_distance(f_lat, f_lng, seen_lat, seen_lng) < 40:
                    if f_name.lower()[:10] in seen_name.lower() or seen_name.lower()[:10] in f_name.lower():
                        is_dup = True
                        break
            if is_dup:
                continue
            seen_coordinates.append((f_lat, f_lng, f_name))

            # Specialty and clinical relevance verification
            raw_type = rec.get("facility_type") or rec.get("category") or "Hospital"
            emergency_flag = rec.get("emergency", "no")
            specialty_check = verify_facility_specialty(
                facility_type=raw_type,
                facility_name=f_name,
                specialty_info=specialty_info,
                is_emergency=emergency_flag,
            )

            fac_category = self._normalize_category(raw_type, category)
            if category != "all" and fac_category != category:
                # If specific category filter requested (e.g. 'hospital'), respect it
                if category == "hospital" and fac_category != "hospital":
                    continue

            fac_id = self._generate_facility_id(f_name, f_lat, f_lng)
            directions_url = build_google_maps_directions_url(f_lat, f_lng)
            maps_url = rec.get("source_url") or build_google_maps_facility_url(f_name, f_lat, f_lng)

            processed.append(
                FacilityResult(
                    id=fac_id,
                    name=f_name,
                    category=fac_category,
                    latitude=f_lat,
                    longitude=f_lng,
                    address=rec.get("address"),
                    phone=rec.get("phone"),
                    website=rec.get("website"),
                    opening_hours=rec.get("opening_hours"),
                    emergency=emergency_flag,
                    specialty=specialty_check.get("verified_specialty") or specialty_info.get("specialty_name"),
                    rating=rec.get("rating"),
                    review_count=rec.get("review_count"),
                    distance_meters=dist_meters,
                    distance_formatted=format_distance(dist_meters),
                    source_url=rec.get("source_url"),
                    maps_url=maps_url,
                    directions_url=directions_url,
                    source="google-maps-scraper",
                )
            )

        # STRICT GEOGRAPHICAL DISTANCE RANKING: Nearest First
        # If emergency priority is active, verified emergency facilities are prioritized,
        # but within each group they are strictly sorted by distance.
        if specialty_info.get("emergency_required", False):
            # Sort emergency-capable first, then by distance
            processed.sort(key=lambda f: (0 if f.emergency == "yes" else 1, f.distance_meters))
        else:
            processed.sort(key=lambda f: f.distance_meters)

        return processed[:limit]

    def _execute_search(
        self,
        lat: float,
        lng: float,
        radius: int = 5000,
        limit: int = 5,
        category: str = "all",
        condition_name: Optional[str] = None,
        symptoms: Optional[List[str]] = None,
    ) -> NearbyFacilitiesResponse:
        """Internal synchronous search pipeline."""
        if lat is None or lng is None:
            raise ValueError("Coordinates (latitude, longitude) must be provided. Cannot search without location.")

        validate_coordinates(lat, lng)
        radius = min(max(radius, 500), 20000)
        limit = min(max(limit, 1), 50)

        # Map condition context to targeted medical facility queries
        specialty_info = map_condition_to_facility_query(condition_name, symptoms)
        target_query = specialty_info.get("search_query", "hospitals clinics")

        # Refine query if category is specifically requested
        if category == "hospital":
            target_query = f"{target_query} hospital"
        elif category == "clinic":
            target_query = f"{target_query} clinic"

        search_links = self._build_external_search_links(lat, lng)
        external_dict = {"google_maps": search_links}

        # Check if mock client was injected for testing
        raw_records: List[Dict[str, Any]] = []
        if self._mock_client is not None:
            if hasattr(self._mock_client, "query_nearby"):
                mock_res = self._mock_client.query_nearby(lat, lng, radius_meters=radius)
                if isinstance(mock_res, dict) and mock_res.get("elements"):
                    # Translate mock OSM elements to scraper records if legacy test harness
                    for el in mock_res.get("elements", []):
                        raw_records.append({
                            "name": el.get("tags", {}).get("name", "Mock Facility"),
                            "latitude": el.get("lat", lat),
                            "longitude": el.get("lon", lng),
                            "facility_type": el.get("tags", {}).get("amenity", "hospital"),
                            "phone": el.get("tags", {}).get("phone"),
                            "emergency": el.get("tags", {}).get("emergency", "no"),
                            "source_url": None,
                        })
            elif hasattr(self._mock_client, "scrape_facilities"):
                raw_records = self._mock_client.scrape_facilities(lat, lng, target_query, radius, limit * 2)
        else:
            try:
                raw_records = self.scraper.scrape_facilities(
                    lat=lat,
                    lng=lng,
                    search_query=target_query,
                    radius_meters=radius,
                    max_results=limit * 2,
                )
            except Exception as e:
                logger.error(f"Scraping failed: {e}", exc_info=True)
                raw_records = []

        # Process and rank records
        facilities = self._process_scraped_records(
            raw_records=raw_records,
            user_lat=lat,
            user_lng=lng,
            radius_meters=radius,
            limit=limit,
            category=category,
            specialty_info=specialty_info,
        )

        # Automatic Radius Expansion: If zero results within initial radius and radius < 10000m,
        # expand radius and search nearby area once
        effective_radius = radius
        if not facilities and radius < 10000 and self._mock_client is None:
            effective_radius = 10000
            logger.info(f"Zero facilities found at {radius}m; retrying once with expanded 10000m radius.")
            try:
                expanded_records = self.scraper.scrape_facilities(
                    lat=lat,
                    lng=lng,
                    search_query="hospitals clinics",
                    radius_meters=10000,
                    max_results=limit * 2,
                )
                facilities = self._process_scraped_records(
                    raw_records=expanded_records,
                    user_lat=lat,
                    user_lng=lng,
                    radius_meters=10000,
                    limit=limit,
                    category=category,
                    specialty_info=specialty_info,
                )
            except Exception as e:
                logger.warning(f"Radius expansion search failed: {e}")

        final_status = "success" if facilities else "empty"
        msg = (
            None
            if facilities
            else f"No verified healthcare facilities discovered within {effective_radius}m. Explore the direct Google Maps links below."
        )

        return NearbyFacilitiesResponse(
            facilities=facilities,
            external_search=external_dict,
            source="google-maps-scraper",
            status=final_status,
            message=msg,
            latitude=lat,
            longitude=lng,
            radius_km=effective_radius / 1000.0,
            condition=condition_name,
        )

    def search_nearby(
        self,
        lat: float,
        lng: float,
        radius: int = 5000,
        limit: int = 5,
        category: str = "all",
        condition_name: Optional[str] = None,
        symptoms: Optional[List[str]] = None,
    ) -> NearbyFacilitiesResponse:
        """Synchronous search for nearby facilities around (lat, lng)."""
        return self._execute_search(
            lat=lat,
            lng=lng,
            radius=radius,
            limit=limit,
            category=category,
            condition_name=condition_name,
            symptoms=symptoms,
        )

    async def search_nearby_async(
        self,
        lat: float,
        lng: float,
        radius: int = 5000,
        limit: int = 5,
        category: str = "all",
        condition_name: Optional[str] = None,
        symptoms: Optional[List[str]] = None,
    ) -> NearbyFacilitiesResponse:
        """Asynchronous search for nearby facilities running scraping in worker thread."""
        return await asyncio.to_thread(
            self._execute_search,
            lat,
            lng,
            radius,
            limit,
            category,
            condition_name,
            symptoms,
        )
