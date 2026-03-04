"""
Telemetry API Routes
Exposes session and aggregate token usage metrics.

Endpoints:
- GET /telemetry/session/{session_id} - Get detailed metrics for a session
- GET /telemetry/sessions - Get all session IDs
- GET /telemetry/summary - Get aggregate metrics across all sessions
- DELETE /telemetry/session/{session_id} - Reset a specific session
- DELETE /telemetry/all - Reset all telemetry data
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

# Global telemetry tracker instance
telemetry_tracker = None


def init_telemetry(tracker):
    """Initialize telemetry tracker for routes."""
    global telemetry_tracker
    telemetry_tracker = tracker


router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.get("/session/{session_id}")
async def get_session_telemetry(session_id: str):
    """
    Get detailed telemetry for a specific session.
    
    Returns:
    - Session ID, model, provider
    - Context window usage (tokens & percentage)
    - Token breakdown by category (system, tools, files, messages, results)
    - Performance metrics (response times, error rate)
    - Request summary (total, tool calls, errors)
    
    Example response:
    {
        "session_id": "user123",
        "model": "gpt-4",
        "provider": "openai",
        "context": {
            "window_size": 8192,
            "used_tokens": 2048,
            "used_percent": 25.0,
            "remaining_tokens": 6144
        },
        "token_breakdown": {
            "system_instructions": 50,
            "tool_definitions": 100,
            "file_content": 200,
            "messages": 1500,
            "tool_results": 198,
            "other": 0,
            "total": 2048,
            "percentages": {
                "system_instructions": 2.4,
                "tool_definitions": 4.9,
                "file_content": 9.8,
                "messages": 73.2,
                "tool_results": 9.7,
                "other": 0.0
            }
        },
        "tokens": {
            "input": 1500,
            "output": 548,
            "total": 2048,
            "avg_per_request": 512.0
        },
        "requests": {
            "total": 4,
            "tool_calls": 2,
            "errors": 0,
            "error_rate_percent": 0.0
        },
        "performance": {
            "total_duration_seconds": 12.5,
            "avg_response_time_ms": 3125.0,
            "median_response_time_ms": 3000.0,
            "p95_response_time_ms": 4500.0
        },
        "started_at": "2024-03-04T10:00:00",
        "last_request_at": "2024-03-04T10:00:30"
    }
    """
    if telemetry_tracker is None:
        raise HTTPException(status_code=500, detail="Telemetry tracker not initialized")
    
    summary = telemetry_tracker.get_session_summary(session_id)
    if summary.get("total_requests", 0) == 0 and "message" in summary:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    return summary


@router.get("/sessions")
async def list_sessions():
    """
    Get list of all session IDs.
    
    Returns:
    {
        "sessions": ["user123", "user456", "agent_session_789"],
        "total_sessions": 3
    }
    """
    if telemetry_tracker is None:
        raise HTTPException(status_code=500, detail="Telemetry tracker not initialized")
    
    session_ids = telemetry_tracker.get_session_ids()
    return {
        "sessions": session_ids,
        "total_sessions": len(session_ids)
    }


@router.get("/summary")
async def get_summary():
    """
    Get aggregate telemetry across all sessions.
    
    Returns:
    {
        "total_sessions": 3,
        "total_input_tokens": 5000,
        "total_output_tokens": 2500,
        "total_tokens": 7500,
        "total_requests": 15,
        "total_tool_calls": 8,
        "total_duration_ms": 45000.0,
        "models_used": ["gpt-4", "gpt-3.5-turbo"],
        "providers_used": ["openai"],
        "avg_response_time_ms": 3000.0,
        "token_breakdown": {
            "system_instructions": 500,
            "tool_definitions": 800,
            "file_content": 1000,
            "messages": 4500,
            "tool_results": 700,
            "other": 0,
            "total": 7500,
            "percentages": {
                "system_instructions": 6.7,
                "tool_definitions": 10.7,
                "file_content": 13.3,
                "messages": 60.0,
                "tool_results": 9.3,
                "other": 0.0
            }
        }
    }
    """
    if telemetry_tracker is None:
        raise HTTPException(status_code=500, detail="Telemetry tracker not initialized")
    
    return telemetry_tracker.get_total_summary()


@router.delete("/session/{session_id}")
async def reset_session(session_id: str):
    """Reset telemetry data for a specific session."""
    if telemetry_tracker is None:
        raise HTTPException(status_code=500, detail="Telemetry tracker not initialized")
    
    telemetry_tracker.reset(session_id)
    return {
        "message": f"Session {session_id} telemetry reset",
        "session_id": session_id
    }


@router.delete("/all")
async def reset_all():
    """Reset all telemetry data."""
    if telemetry_tracker is None:
        raise HTTPException(status_code=500, detail="Telemetry tracker not initialized")
    
    telemetry_tracker.reset()
    return {
        "message": "All telemetry data reset",
        "sessions_cleared": len(telemetry_tracker.get_session_ids())
    }
