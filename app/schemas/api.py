from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# --- Session Models ---

class StartSessionRequest(BaseModel):
    initial_message: Optional[str] = Field(default=None, description="Optional starting message from the user")


class StartSessionResponse(BaseModel):
    thread_id: str = Field(description="Unique session ID to pass in subsequent messages")
    message: Optional[str] = Field(default=None, description="Initial greeting or response from agent")


class ChatMessageRequest(BaseModel):
    thread_id: str = Field(description="The active session thread ID")
    message: str = Field(default="", description="The user's message text", max_length=2000)
    action_id: Optional[str] = Field(default=None, description="Optional post-assessment action ID e.g. GET_AYURVEDIC_GUIDANCE or FIND_NEARBY_CLINICS")
    condition_id: Optional[str] = Field(default=None, description="Selected condition ID for the action")
    latitude: Optional[float] = Field(default=None, description="Optional latitude for facility discovery")
    longitude: Optional[float] = Field(default=None, description="Optional longitude for facility discovery")


class ActionExecutionRequest(BaseModel):
    thread_id: str = Field(description="Active session thread ID")
    action_id: str = Field(description="Action identifier e.g. GET_AYURVEDIC_GUIDANCE or FIND_NEARBY_CLINICS")
    condition_id: Optional[str] = Field(default=None, description="Target condition ID from assessment")
    latitude: Optional[float] = Field(default=None, description="Optional latitude")
    longitude: Optional[float] = Field(default=None, description="Optional longitude")


class CitationSource(BaseModel):
    title: str
    id: str
    tag: Optional[str] = "WHO"


class ConditionCandidateSchema(BaseModel):
    condition_id: str
    name: str
    explanation: str
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    findings_against: Optional[str] = None
    uncertainties: Optional[str] = None
    recommended_care_setting: Optional[str] = None


class RecommendedActionSchema(BaseModel):
    action: str
    rationale: str
    supporting_evidence_ids: List[str] = Field(default_factory=list)


class StructuredAssessment(BaseModel):
    case_summary: str
    possible_conditions: List[ConditionCandidateSchema] = Field(default_factory=list)
    recommended_actions: List[RecommendedActionSchema] = Field(default_factory=list)
    warning_signs: List[str] = Field(default_factory=list)
    sources: List[CitationSource] = Field(default_factory=list)
    evidence_limitations: List[str] = Field(default_factory=list)


class PostAssessmentAction(BaseModel):
    id: str
    label: str
    condition_id: str


class ChatMessageResponse(BaseModel):
    message: str = Field(description="The AI agent's response")
    is_complete: bool = Field(default=False, description="True if a final diagnosis/remedy was reached")
    stage: str = Field(description="The current internal stage of the triage graph")
    symptom_facts: Dict[str, Any] = Field(default_factory=dict, description="Current known facts about the patient")
    risk_level: Optional[str] = Field(default="not_assessed", description="Clinical risk rating (not_assessed, low, medium, high, emergency)")
    confidence: Optional[float] = Field(default=0.95, description="Diagnostic confidence score 0.0-1.0")
    sources: List[CitationSource] = Field(default_factory=list, description="Clinical reference sources")
    assessment_id: Optional[str] = Field(default=None, description="Database ID of saved assessment")
    assessment: Optional[StructuredAssessment] = Field(default=None, description="Structured clinical triage assessment")
    actions: List[PostAssessmentAction] = Field(default_factory=list, description="Next selectable post-assessment actions")
    facilities: Optional[List[Dict[str, Any]]] = Field(default=None, description="Structured nearby facilities")
    external_search: Optional[Dict[str, Any]] = Field(default=None, description="External maps search links")
    ayurvedic_guidance: Optional[Dict[str, Any]] = Field(default=None, description="Structured Ayurvedic clinical guidance")


class SessionItem(BaseModel):
    id: str
    thread_id: str
    title: str
    created_at: float
    updated_at: float
    message_count: int = 0


class SessionListResponse(BaseModel):
    sessions: List[SessionItem] = Field(default_factory=list)


class HistoricalMessage(BaseModel):
    id: str
    role: str  # 'user' | 'bot'
    text: str
    timestamp: str
    stage: Optional[str] = None
    is_complete: Optional[bool] = False
    symptom_facts: Optional[Dict[str, Any]] = None
    assessment: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    sources: Optional[List[Dict[str, Any]]] = None
    facilities: Optional[List[Dict[str, Any]]] = None
    external_search: Optional[Dict[str, Any]] = None


class SessionHistoryResponse(BaseModel):
    thread_id: str
    messages: List[HistoricalMessage] = Field(default_factory=list)
    symptom_facts: Dict[str, Any] = Field(default_factory=dict)
    stage: str = "unknown"
    status: Optional[str] = "unknown"
    assessment: Optional[Dict[str, Any]] = None


# --- Ambulance / Hospital Models ---

class AmbulanceProvider(BaseModel):
    id: str
    name: str
    type: str
    distance: str
    eta: str
    phone: str
    status: str
    driver: str
    vehicleNo: str


class NearbyAmbulancesResponse(BaseModel):
    latitude: float
    longitude: float
    providers: List[AmbulanceProvider]


# --- User Profile & Settings Models ---

class UserProfile(BaseModel):
    user_id: str
    name: str = "Prashik K."
    email: str = "prashik@ragblucare.ai"
    phone: str = "+91 94038 71129"
    dob: str = "October 14, 1998"
    bloodGroup: str = "O Positive (O+)"
    allergies: str = "Penicillin, Dust Mites"
    emergencyContact: str = "Sanket K. (+91 98765 43210)"


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    dob: Optional[str] = None
    bloodGroup: Optional[str] = None
    allergies: Optional[str] = None
    emergencyContact: Optional[str] = None


class UserSettings(BaseModel):
    user_id: str
    selectedProtocol: str = "standard-care"
    sensitivity: str = "85"


class UserSettingsUpdate(BaseModel):
    selectedProtocol: Optional[str] = None
    sensitivity: Optional[str] = None


# --- Document Upload Models ---

class DocumentUploadResponse(BaseModel):
    filename: str
    extracted_text: str
    summary: str
    detected_symptoms: List[str] = Field(default_factory=list)
