from typing import List, Optional
from app.facilities.schemas import EmergencyContact, EmergencyDirectoryResponse

VERIFIED_EMERGENCY_CONTACTS: List[EmergencyContact] = [
    EmergencyContact(
        country="India",
        region="National (All States & UTs)",
        number="112",
        service="ERSS (All-in-One Emergency: Police, Fire, Health & Ambulance)",
        official_source="https://112.gov.in/",
        last_verification_date="2026-11",
        verification_status="verified",
        notes="Pan-India single emergency response support system, accessible 24/7 without SIM or credit."
    ),
    EmergencyContact(
        country="India",
        region="National / Participating States",
        number="108",
        service="Emergency Medical Response Ambulance Service",
        official_source="https://nhm.gov.in/",
        last_verification_date="2026-11",
        verification_status="verified",
        notes="Toll-free emergency medical transit and trauma response service under National Health Mission."
    ),
    EmergencyContact(
        country="India",
        region="National / Participating States",
        number="102",
        service="Maternal & Neonatal Transport Ambulance Service",
        official_source="https://nhm.gov.in/",
        last_verification_date="2026-11",
        verification_status="verified",
        notes="Free transport service primarily dedicated to pregnant women and sick infants."
    ),
    EmergencyContact(
        country="United States",
        region="National",
        number="911",
        service="Integrated Emergency Response (Police, Fire, EMS)",
        official_source="https://www.fcc.gov/general/9-1-1-and-e9-1-1-services",
        last_verification_date="2026-11",
        verification_status="verified",
        notes="Universal 24/7 emergency dispatch service in the United States."
    ),
    EmergencyContact(
        country="United Kingdom",
        region="National",
        number="999",
        service="Emergency Services (Ambulance, Police, Fire)",
        official_source="https://www.nhs.uk/using-the-nhs/healthcare-services/urgent-and-emergency-care-services/when-to-call-999/",
        last_verification_date="2026-11",
        verification_status="verified",
        notes="Primary emergency number for life-threatening conditions."
    ),
    EmergencyContact(
        country="United Kingdom",
        region="National",
        number="111",
        service="NHS 111 (Urgent Non-Emergency Medical Advice)",
        official_source="https://111.nhs.uk/",
        last_verification_date="2026-11",
        verification_status="verified",
        notes="Free 24/7 medical advice helpline for urgent health concerns that are not life-threatening."
    ),
]


def get_emergency_contacts(country: Optional[str] = None, region: Optional[str] = None) -> EmergencyDirectoryResponse:
    """Returns verified emergency contact directory optionally filtered by country or region."""
    contacts = VERIFIED_EMERGENCY_CONTACTS
    if country and country.strip():
        c_norm = country.strip().lower()
        filtered = [c for c in contacts if c.country.lower() == c_norm]
        if filtered:
            contacts = filtered

    return EmergencyDirectoryResponse(
        contacts=contacts,
        disclaimer=(
            "Emergency telephone services are managed directly by respective national/regional government authorities. "
            "BluCare+ provides this verified directory strictly for informational guidance and does not dispatch emergency services."
        )
    )
