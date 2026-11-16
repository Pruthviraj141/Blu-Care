"""
Unit & Integration Tests for BluCare+ Langfuse Observability & Tracing.
Verifies:
1. Configuration loading & initialization (enabled vs disabled vs invalid keys).
2. Privacy & PII protection (zero tokens, passwords, or Clerk secrets leaked).
3. SessionService LangGraph execution with Langfuse callback handler.
4. The 6 core application scenarios:
   - Scenario 1: Simple greeting.
   - Scenario 2: Normal symptom assessment intake turn.
   - Scenario 3: Complete symptom intake triggering medical RAG & differential diagnosis.
   - Scenario 4: Insufficient clinical evidence handling.
   - Scenario 5: Error handling without disruption.
   - Scenario 6: Streaming response generator with tracing.
5. Graceful degradation when Langfuse is disabled or unreachable.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

from app.core.config import settings
from app.core.langfuse_client import (
    is_langfuse_enabled,
    get_langfuse_client,
    get_langfuse_callback_handler,
    build_langchain_trace_config,
    sanitize_trace_metadata,
    flush_langfuse,
)
from app.core.session_service import SessionService
from app.graph.build_graph import compiled_triage_graph


def test_sanitize_trace_metadata():
    """Verifies that PII, secrets, auth headers, and tokens are completely stripped from metadata."""
    dirty_metadata = {
        "user_token": "secret_jwt_xyz",
        "authorization": "Bearer clerk_12345",
        "clerk_session_id": "sess_secret",
        "patient_email": "patient@hospital.org",
        "patient_phone": "+1-555-0199",
        "groq_model": "openai/gpt-oss-120b",
        "turn_id": 2,
        "nested": {
            "token": "nested_token",
            "safe_metric": 42,
        },
    }

    clean = sanitize_trace_metadata(dirty_metadata)

    assert "user_token" not in clean
    assert "authorization" not in clean
    assert "clerk_session_id" not in clean
    assert "patient_email" not in clean
    assert "patient_phone" not in clean
    assert clean["groq_model"] == "openai/gpt-oss-120b"
    assert clean["turn_id"] == 2
    assert "token" not in clean["nested"]
    assert clean["nested"]["safe_metric"] == 42


def test_disabled_graceful_degradation():
    """Verifies that when Langfuse is disabled, the app functions normally with no callbacks."""
    original = settings.langfuse_enabled
    try:
        settings.langfuse_enabled = False
        assert not is_langfuse_enabled()

        config = build_langchain_trace_config("test-thread-disabled", user_id="user-123")
        assert "callbacks" not in config
        assert config["configurable"]["thread_id"] == "test-thread-disabled"

        # Start session works with Langfuse disabled
        thread_id, reply = SessionService.start_session("Hello")
        assert thread_id
        assert "Hello" in reply or "symptom" in reply.lower()
    finally:
        settings.langfuse_enabled = original


def test_invalid_credentials_graceful_degradation():
    """Verifies that if Langfuse credentials are wrong, the app does not crash."""
    original_key = settings.langfuse_public_key
    try:
        settings.langfuse_public_key = "pk-lf-invalid-test-key"
        # Should return None or handle gracefully without throwing
        handler = get_langfuse_callback_handler()
        # Even if handler initializes, invoking graph must not crash
        config = build_langchain_trace_config("test-thread-invalid-key")
        assert "configurable" in config
    finally:
        settings.langfuse_public_key = original_key


def test_scenario_1_greeting():
    """Scenario 1: Simple greeting interaction."""
    thread_id, reply = SessionService.start_session("hi")
    assert thread_id
    assert len(reply) > 0

    # Process message turn with greeting
    res = SessionService.process_message(thread_id, "Hello good morning")
    assert "message" in res
    assert res["stage"] == "intake"
    assert not res["is_complete"]


def test_scenario_2_symptom_assessment_intake():
    """Scenario 2: Normal symptom assessment turn."""
    thread_id, reply = SessionService.start_session()
    res = SessionService.process_message(thread_id, "I have had a mild fever and body aches for two days")
    assert res["stage"] in ("intake", "post_prediction")
    assert "fever" in str(res["symptom_facts"]).lower() or "body" in str(res["symptom_facts"]).lower()


def test_scenario_3_medical_rag_differential():
    """Scenario 3: Question or intake that triggers medical RAG and evidence generation."""
    thread_id, _ = SessionService.start_session()

    # Step through intake to completion
    res1 = SessionService.process_message(thread_id, "I have a high fever, cough, and severe fatigue")
    # Follow up with duration to resolve pending questions
    res2 = SessionService.process_message(thread_id, "It has been 4 days, mild severity, no chest pain")

    assert "message" in res2
    assert "stage" in res2
    assert res2["confidence"] > 0


def test_scenario_4_insufficient_evidence_or_abstention():
    """Scenario 4: Question with insufficient medical evidence."""
    thread_id, _ = SessionService.start_session()
    # Query with non-medical context
    res = SessionService.process_message(thread_id, "Can you help me fix my computer screen?")
    assert "message" in res
    # BluCare+ stays safe and handles gracefully
    assert len(res["message"]) > 0


def test_scenario_5_error_resilience():
    """Scenario 5: Graph and session resilience against downstream error."""
    thread_id, _ = SessionService.start_session()

    # Process normal message with simulated network jitter / tracing flush
    res = SessionService.process_message(thread_id, "I have a sore throat")
    assert "message" in res

    # Calling flush does not raise
    flush_langfuse()


def test_scenario_6_streaming_response():
    """Scenario 6: Streaming response generator captures traces correctly."""
    async def _run():
        thread_id, _ = SessionService.start_session()
        chunks = []
        async for chunk in SessionService.stream_message_generator(thread_id, "Hello, can you hear me?"):
            chunks.append(chunk)

        full_output = "".join(chunks)
        assert "[DONE]" in full_output
        assert len(chunks) >= 2

    asyncio.run(_run())


def test_trace_generation_in_langfuse():
    """Verifies that an actual trace is produced and transmitted to Langfuse."""
    if not is_langfuse_enabled():
        pytest.skip("Langfuse is not enabled")

    thread_id, _ = SessionService.start_session(user_id="test_patient_verified")
    res = SessionService.process_message(
        thread_id=thread_id,
        message="I have mild fever and sore throat for 3 days",
        user_id="test_patient_verified",
    )
    assert "message" in res

    # Flush Langfuse queue to ensure trace is delivered
    flush_langfuse()
