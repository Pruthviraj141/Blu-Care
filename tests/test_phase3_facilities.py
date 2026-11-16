import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings

settings.allow_dev_auth = True
settings.app_env = "testing"

from app.facilities.distance import haversine_distance, format_distance
from app.facilities.maps_urls import (
    build_google_maps_search_url,
    build_google_maps_facility_url,
    build_google_maps_directions_url,
    validate_coordinates,
)
from app.facilities.service import FacilitiesService
from app.facilities.scraper import HospitalScraper
from app.facilities.specialty_mapper import (
    map_condition_to_facility_query,
    verify_facility_specialty,
)
from app.facilities.emergency_contacts import get_emergency_contacts
from app.rag.tools.facilities_tool import find_nearby_facilities
from app.db.session import init_db

client = TestClient(app, headers={"Authorization": "Bearer test_dev_token"})


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_db()


# =====================================================================
# 1. DISTANCE & HAVERSINE TESTS
# =====================================================================

def test_haversine_distance_identical_points():
    dist = haversine_distance(18.5204, 73.8567, 18.5204, 73.8567)
    assert dist == 0.0


def test_haversine_distance_known_coordinates():
    # Pune (18.5204, 73.8567) to Mumbai (18.9388, 72.8354) is ~120 km
    dist = haversine_distance(18.5204, 73.8567, 18.9388, 72.8354)
    assert 115000 <= dist <= 125000


def test_haversine_coordinate_validation():
    with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
        haversine_distance(95.0, 73.0, 18.0, 73.0)
    with pytest.raises(ValueError, match="Longitude must be between -180 and 180"):
        haversine_distance(18.0, -190.0, 18.0, 73.0)


def test_format_distance():
    assert format_distance(450.0) == "450 m"
    assert format_distance(1200.0) == "1.2 km"
    assert format_distance(5480.0) == "5.5 km"


# =====================================================================
# 2. GOOGLE MAPS URL BUILDER TESTS
# =====================================================================

def test_build_google_maps_search_url():
    url = build_google_maps_search_url(18.5204, 73.8567, "hospitals")
    assert "https://www.google.com/maps/search/?" in url
    assert "api=1" in url
    assert "hospitals+near+18.5204%2C73.8567" in url or "hospitals+near+18.5204,73.8567" in url


def test_build_google_maps_url_disallows_invalid_categories():
    with pytest.raises(ValueError, match="Invalid category"):
        build_google_maps_search_url(18.5204, 73.8567, "bars")


def test_build_google_maps_url_rejects_symptoms_or_pii():
    url = build_google_maps_search_url(18.5204, 73.8567, "clinics")
    assert "symptom" not in url.lower()
    assert "fever" not in url.lower()
    assert "patient" not in url.lower()


def test_build_google_maps_facility_and_directions_urls():
    fac_url = build_google_maps_facility_url("SPARSH Hospital", 12.9832, 77.5947)
    assert "SPARSH+Hospital" in fac_url or "SPARSH Hospital" in fac_url
    assert "api=1" in fac_url

    dir_url = build_google_maps_directions_url(12.9832, 77.5947)
    assert "https://www.google.com/maps/dir/?" in dir_url
    assert "destination=12.9832%2C77.5947" in dir_url or "destination=12.9832,77.5947" in dir_url


# =====================================================================
# 3. SCRAPER DATA EXTRACTION & CARD PARSING TESTS
# =====================================================================

def test_scraper_card_extraction_parses_coordinates_and_metadata():
    scraper = HospitalScraper()

    # Mock Selenium card element
    mock_card = MagicMock()
    mock_name_el = MagicMock()
    mock_name_el.text = "SPARSH Hospital"

    mock_link_el = MagicMock()
    mock_link_el.get_attribute.side_effect = lambda attr: (
        "https://www.google.com/maps/place/SPARSH+Hospital/data=!4m7!3m6!1s0x3bae1662b5e4f303:0x83e17841b11f5631!8m2!3d12.9832825!4d77.59475!16s%2Fg%2F11b69swnm9"
        if attr == "href" else "SPARSH Hospital"
    )

    mock_rating_el = MagicMock()
    mock_rating_el.text = "4.6"
    mock_rev_el = MagicMock()
    mock_rev_el.text = "(5,462)"

    def mock_find_element(by, sel):
        if sel in (".qBF1Pd", ".fontHeadlineSmall"):
            return mock_name_el
        if sel == "a.hfpxzc":
            return mock_link_el
        if sel == "span.MW4etd":
            return mock_rating_el
        if sel == "span.UY7F9":
            return mock_rev_el
        raise Exception("Not found")

    mock_card.find_element.side_effect = mock_find_element
    mock_card.text = (
        "SPARSH Hospital\nSPARSH Hospital\n4.6(5,462)\n"
        "General hospital · Infantry Rd, Bengaluru\n"
        "Open 24 hours · 080 6591 3403\nWebsite\nDirections"
    )

    record = scraper._extract_card_data(mock_card)
    assert record is not None
    assert record["name"] == "SPARSH Hospital"
    assert record["latitude"] == 12.9832825
    assert record["longitude"] == 77.59475
    assert record["rating"] == 4.6
    assert record["review_count"] == 5462
    assert record["facility_type"] == "General hospital"
    assert record["phone"] == "080 6591 3403"
    assert record["emergency"] == "yes"
    assert "Infantry Rd" in record["address"]


# =====================================================================
# 4. DISEASE-AWARE SPECIALTY MAPPING & CLINICAL VERIFICATION
# =====================================================================

def test_specialty_mapping_cardiac_condition():
    info = map_condition_to_facility_query("Severe chest pain radiating to left arm")
    assert info["condition_id"] == "cardiac"
    assert "cardiac hospital" in info["search_query"].lower()
    assert info["emergency_required"] is True

    # Check verification: Heart hospital is verified
    res_heart = verify_facility_specialty("Heart hospital", "Wadia Cardiac Center", info, "yes")
    assert res_heart["is_relevant"] is True

    # Check verification: Dental clinic is NOT verified for cardiac symptoms
    res_dental = verify_facility_specialty("Dental clinic", "Bright Smile Dental", info, "no")
    assert res_dental["is_relevant"] is False


def test_specialty_mapping_orthopedic_condition():
    info = map_condition_to_facility_query("Fracture after road accident with bone trauma")
    assert info["condition_id"] == "orthopedic"
    assert "orthopedic" in info["search_query"].lower()

    res_ortho = verify_facility_specialty("Orthopedic clinic", "HOSMAT Ortho", info, "yes")
    assert res_ortho["is_relevant"] is True


def test_specialty_mapping_fever_and_general():
    info = map_condition_to_facility_query("High fever with viral chills")
    assert info["condition_id"] == "fever"
    assert "clinic" in info["search_query"].lower() or "physician" in info["search_query"].lower()

    res_clinic = verify_facility_specialty("Medical clinic", "Hansaa Clinic", info, "no")
    assert res_clinic["is_relevant"] is True


# =====================================================================
# 5. FACILITIES SERVICE PIPELINE & NEAREST-FIRST RANKING TESTS
# =====================================================================

SAMPLE_SCRAPED_FACILITIES = [
    {
        "name": "Far Away Specialized Hospital",
        "latitude": 18.5700,
        "longitude": 73.8900,
        "facility_type": "Hospital",
        "address": "Camp Road, Pune",
        "phone": "+91 20 11112222",
        "emergency": "yes",
        "rating": 4.8,
        "review_count": 920,
        "source_url": "https://maps.google.com/?cid=1",
    },
    {
        "name": "Close Local Medical Clinic",
        "latitude": 18.5220,
        "longitude": 73.8580,
        "facility_type": "Medical clinic",
        "address": "Shivajinagar, Pune",
        "phone": "+91 20 33334444",
        "emergency": "no",
        "rating": 4.2,
        "review_count": 140,
        "source_url": "https://maps.google.com/?cid=2",
    },
    {
        "name": "Mid Distance General Hospital",
        "latitude": 18.5350,
        "longitude": 73.8650,
        "facility_type": "General hospital",
        "address": "FC Road, Pune",
        "phone": "+91 20 55556666",
        "emergency": "yes",
        "rating": 4.5,
        "review_count": 2100,
        "source_url": "https://maps.google.com/?cid=3",
    },
    {
        # Near duplicate of Close Local Medical Clinic within 20 meters
        "name": "Close Local Medical Clinic OPD",
        "latitude": 18.5221,
        "longitude": 73.8581,
        "facility_type": "Medical clinic",
        "address": "Shivajinagar, Pune",
        "phone": "+91 20 33334444",
        "emergency": "no",
        "source_url": "https://maps.google.com/?cid=2_dup",
    },
]


def test_facilities_service_sorts_strictly_nearest_first_and_deduplicates():
    user_lat, user_lng = 18.5204, 73.8567
    service = FacilitiesService()

    with patch.object(service.scraper, "scrape_facilities", return_value=SAMPLE_SCRAPED_FACILITIES):
        res = service.search_nearby(lat=user_lat, lng=user_lng, radius=10000, condition_name="fever")
        assert res.status == "success"
        # Deduplication removes the 20m duplicate
        assert len(res.facilities) == 3

        # Strict distance order validation (Nearest First)
        distances = [f.distance_meters for f in res.facilities]
        assert distances == sorted(distances)
        assert res.facilities[0].name == "Close Local Medical Clinic"
        assert res.facilities[0].distance_meters < 300  # under 300m away
        assert res.facilities[-1].name == "Far Away Specialized Hospital"

        # Check turn-by-turn directions URLs
        for f in res.facilities:
            assert f.directions_url is not None
            assert "https://www.google.com/maps/dir/?" in f.directions_url
            assert f"destination={f.latitude}" in f.directions_url


def test_facilities_service_location_change_changes_ranking():
    # User in Pune
    pune_lat, pune_lng = 18.5204, 73.8567
    # User in Mumbai
    mumbai_lat, mumbai_lng = 19.0760, 72.8777

    service = FacilitiesService()
    with patch.object(service.scraper, "scrape_facilities", return_value=SAMPLE_SCRAPED_FACILITIES):
        pune_res = service.search_nearby(lat=pune_lat, lng=pune_lng, radius=5000)
        assert len(pune_res.facilities) > 0
        assert pune_res.facilities[0].distance_meters < 5000

        # When searching from Mumbai, Pune facilities (>100km away) are strictly excluded by radius
        mumbai_res = service.search_nearby(lat=mumbai_lat, lng=mumbai_lng, radius=5000)
        assert len(mumbai_res.facilities) == 0


def test_facilities_service_validates_coordinates_no_hardcoded_fallback():
    service = FacilitiesService()
    with pytest.raises(ValueError, match="Coordinates .* must be provided"):
        service.search_nearby(lat=None, lng=77.5946)

    with pytest.raises(ValueError, match="Invalid latitude"):
        service.search_nearby(lat=100.5, lng=77.5946)


def test_facilities_service_expands_radius_when_initial_empty():
    user_lat, user_lng = 18.5204, 73.8567
    service = FacilitiesService()

    # First call at 5000m returns empty, second call at 10000m returns facilities
    def mock_scrape(lat, lng, search_query, radius_meters, max_results):
        if radius_meters == 5000:
            return []
        return SAMPLE_SCRAPED_FACILITIES[:2]

    with patch.object(service.scraper, "scrape_facilities", side_effect=mock_scrape):
        res = service.search_nearby(lat=user_lat, lng=user_lng, radius=5000)
        assert res.status == "success"
        assert len(res.facilities) == 2
        assert res.radius_km == 10.0


# =====================================================================
# 6. FASTAPI ENDPOINT TESTS (/api/v1/hospitals/nearby)
# =====================================================================

def test_api_hospitals_nearby_valid_request():
    with patch("app.facilities.service.HospitalScraper.scrape_facilities", return_value=SAMPLE_SCRAPED_FACILITIES):
        resp = client.get("/api/v1/hospitals/nearby?lat=18.5204&lng=73.8567&radius_km=5&condition=cardiac")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["latitude"] == 18.5204
        assert data["longitude"] == 73.8567
        assert data["radius_km"] == 5.0
        assert data["condition"] == "cardiac"
        assert len(data["facilities"]) > 0
        assert "google_maps" in data["external_search"]
        assert data["external_search"]["google_maps"]["hospitals_url"] is not None
        assert len(data["providers"]) > 0


def test_api_hospitals_nearby_rejects_invalid_coordinates():
    resp = client.get("/api/v1/hospitals/nearby?lat=195.0&lng=73.8567")
    assert resp.status_code == 422 or resp.status_code == 400


def test_api_emergency_contacts_endpoint():
    resp = client.get("/api/v1/hospitals/emergency-contacts?country=India")
    assert resp.status_code == 200
    data = resp.json()
    assert "contacts" in data
    assert any(c["number"] == "112" for c in data["contacts"])


# =====================================================================
# 7. RAG TOOL VERIFICATION
# =====================================================================

def test_rag_find_nearby_facilities_tool():
    with patch("app.facilities.service.HospitalScraper.scrape_facilities", return_value=SAMPLE_SCRAPED_FACILITIES):
        output = find_nearby_facilities.invoke({
            "disease": "chest pain",
            "facility_type": "hospital",
            "lat": 18.5204,
            "lon": 73.8567,
        })
        assert "Nearby Healthcare Facilities" in output
        assert "Turn-by-Turn Directions" in output or "Google Maps" in output
        assert "OpenStreetMap" not in output
