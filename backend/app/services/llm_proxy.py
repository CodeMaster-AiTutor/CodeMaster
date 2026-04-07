import os
from typing import Any, Dict
import requests


def _llm_base_url() -> str:
    return os.getenv("LLM_SERVICE_URL", "").strip().rstrip("/")


def _llm_timeout_seconds() -> int:
    raw = os.getenv("LLM_SERVICE_TIMEOUT_SECONDS", "90").strip()
    try:
        return max(5, int(raw))
    except Exception:
        return 90


def _internal_service_key() -> str:
    return os.getenv("LLM_SERVICE_INTERNAL_KEY", "").strip()


def use_external_llm_service() -> bool:
    raw = os.getenv("USE_EXTERNAL_LLM_SERVICE", "false").strip().lower()
    return raw in ("1", "true", "yes", "on")


def call_llm_service(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    base = _llm_base_url()
    if not base:
        raise RuntimeError("LLM_SERVICE_URL is not configured")
    url = f"{base}/{path.lstrip('/')}"
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    internal_key = _internal_service_key()
    if internal_key:
        headers["X-LLM-Service-Key"] = internal_key
    response = requests.post(url, json=payload, headers=headers, timeout=_llm_timeout_seconds())
    try:
        data = response.json()
    except Exception:
        data = {"error": f"Invalid response from LLM service: HTTP {response.status_code}"}
    if response.status_code >= 400:
        error_message = data.get("error") if isinstance(data, dict) else None
        raise RuntimeError(error_message or f"LLM service failed with HTTP {response.status_code}")
    if not isinstance(data, dict):
        raise RuntimeError("LLM service returned unexpected payload")
    return data
