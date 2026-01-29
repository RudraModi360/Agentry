"""
Local metrics - lightweight logging for development (LOCAL MODE).
"""
import logging
from typing import Dict, Any
from datetime import datetime

from .base import MetricsBase

logger = logging.getLogger("agentry.metrics")


class LocalMetrics(MetricsBase):
    """
    Simple logging-based metrics for local development.
    Logs to console/file, no persistent storage.
    """
    
    def __init__(self):
        self._request_count = 0
        self._total_latency = 0.0
    
    async def log_request(self, user_id: str, endpoint: str, method: str,
                         latency_ms: float, **kwargs) -> None:
        """Log a request metric."""
        self._request_count += 1
        self._total_latency += latency_ms
        
        # Log to console in development
        extra_info = " ".join(f"{k}={v}" for k, v in kwargs.items() if v is not None)
        logger.info(
            f"[Metrics] user={user_id} {method} {endpoint} latency={latency_ms:.2f}ms {extra_info}"
        )
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get aggregated stats for a user."""
        return {
            "message": "Detailed per-user metrics available in CLOUD MODE only",
            "mode": "local"
        }
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide stats (in-memory only for local mode)."""
        avg_latency = self._total_latency / self._request_count if self._request_count > 0 else 0
        
        return {
            "mode": "local",
            "session_requests": self._request_count,
            "avg_latency_ms": round(avg_latency, 2),
            "note": "Stats reset on server restart. Use CLOUD MODE for persistent metrics."
        }
