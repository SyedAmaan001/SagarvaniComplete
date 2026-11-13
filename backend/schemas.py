"""Response schemas for the conversational / voice endpoints."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatError(BaseModel):
    code: str
    message: str


class ChatResponse(BaseModel):
    """Structured reply of /api/orca/chat. Legacy keys (understanding_chips,
    active_context, pipeline_result, ...) are kept for the existing dashboard."""

    request_id: str
    conversation_id: str
    session_id: str                       # legacy alias of conversation_id
    user_text: str                        # recognised / typed user text
    assistant_text: str                   # what Sagarvani says
    intent: str                           # conversational intent (greeting, weather, ...)
    status: str = "ok"                    # ok | needs_info | degraded | error
    uses_mock_data: bool = False
    mock_components: List[str] = Field(default_factory=list)
    data_sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: Optional[float] = None
    follow_up_questions: List[str] = Field(default_factory=list)
    errors: List[ChatError] = Field(default_factory=list)

    # legacy / dashboard fields
    query: Optional[str] = None
    english_query: Optional[str] = None
    detected_language: Optional[str] = None
    target_language: Optional[str] = None
    pipeline_intent: Optional[str] = None
    intent_schema: Optional[Dict[str, Any]] = None
    understanding_chips: Optional[List[Dict[str, Any]]] = None
    active_context: Optional[Dict[str, Any]] = None
    pipeline_result: Optional[Dict[str, Any]] = None


class STTResponse(BaseModel):
    request_id: str
    text: str
    mode: str                             # "real" | "mock"
    is_mock: bool
    provider: str
    status: str                           # ok | fallback_to_mock
    language: Optional[str] = None
    duration_sec_estimate: Optional[float] = None
    bytes_received: int
    warning: Optional[str] = None
    interpretation: Optional[Dict[str, Any]] = None


class TTSRequest(BaseModel):
    text: str
    language: str = "en"
    voice: Optional[str] = None


class TTSResponse(BaseModel):
    request_id: str
    mode: str                             # "provider" (audio_base64 present) | "browser" (client speaks)
    is_provider_audio: bool
    provider: str
    language: str
    chunks: List[str]                     # text split for long responses
    audio_base64: List[str] = Field(default_factory=list)   # one per chunk (provider mode)
    mime_type: Optional[str] = None
    warning: Optional[str] = None
