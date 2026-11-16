from typing import Optional
from fastapi import APIRouter

from app.api.v1.endpoints.session import router as session_router
from app.api.v1.endpoints.hospitals import router as hospitals_router
from app.api.v1.endpoints.assessments import router as assessments_router
from app.api.v1.endpoints.user import router as user_router
from app.api.v1.endpoints.upload import router as upload_router
from app.facilities.emergency_contacts import get_emergency_contacts
from app.facilities.schemas import EmergencyDirectoryResponse

api_v1_router = APIRouter()

api_v1_router.include_router(session_router)
api_v1_router.include_router(hospitals_router)
api_v1_router.include_router(assessments_router)
api_v1_router.include_router(user_router)
api_v1_router.include_router(upload_router)


@api_v1_router.get(
    "/emergency-contacts",
    response_model=EmergencyDirectoryResponse,
    tags=["Emergency Directory"],
)
async def api_emergency_contacts(
    country: Optional[str] = None,
    region: Optional[str] = None,
):
    """Authoritative endpoint returning verified emergency service telephone numbers."""
    return get_emergency_contacts(country=country, region=region)
