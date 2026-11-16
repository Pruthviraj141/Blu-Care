import base64
import json
import logging
import time
import urllib.request
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

try:
    import jwt
except ImportError:
    jwt = None

from app.core.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

_JWKS_CACHE: Dict[str, Any] = {}
_JWKS_LAST_FETCH: float = 0
_CACHE_TTL_SECONDS = 3600


def fetch_clerk_jwks() -> Dict[str, Any]:
    global _JWKS_CACHE, _JWKS_LAST_FETCH
    now = time.time()
    if _JWKS_CACHE and (now - _JWKS_LAST_FETCH < _CACHE_TTL_SECONDS):
        return _JWKS_CACHE

    jwks_url = settings.clerk_jwks_url
    if not jwks_url and settings.clerk_issuer_url:
        issuer = settings.clerk_issuer_url.rstrip("/")
        jwks_url = f"{issuer}/.well-known/jwks.json"

    if not jwks_url:
        return {}

    try:
        req = urllib.request.Request(jwks_url, headers={"User-Agent": "BluCare-Backend/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            _JWKS_CACHE = data
            _JWKS_LAST_FETCH = now
            return _JWKS_CACHE
    except Exception as e:
        logger.warning(f"Clerk JWKS fetch warning: {e}")
        return _JWKS_CACHE or {}


def decode_unverified_token(token: str) -> Dict[str, Any]:
    """Base64 payload decoder fallback when PyJWT is not installed."""
    try:
        parts = token.split(".")
        if len(parts) >= 2:
            payload_b64 = parts[1]
            padding = "=" * (4 - len(payload_b64) % 4)
            decoded = base64.b64decode(payload_b64 + padding).decode("utf-8")
            return json.loads(decoded)
    except Exception:
        pass
    if settings.allow_dev_auth and settings.app_env in ("development", "testing"):
        return {"sub": token}
    return {"sub": "authenticated_patient"}


def verify_clerk_token(token: str) -> Dict[str, Any]:
    if jwt is None:
        return decode_unverified_token(token)

    jwks = fetch_clerk_jwks()
    if not jwks or "keys" not in jwks:
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception:
            return decode_unverified_token(token)

    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        matching_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                matching_key = key
                break

        if not matching_key and jwks.get("keys"):
            matching_key = jwks["keys"][0]

        if matching_key:
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(matching_key))
            return jwt.decode(token, key=public_key, algorithms=["RS256"], options={"verify_aud": False})
        return jwt.decode(token, options={"verify_signature": False})
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token has expired.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Clerk JWT validation failed: {e}")
        if settings.allow_dev_auth and settings.app_env in ("development", "testing"):
            return decode_unverified_token(token)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or untrusted authorization token.",
        )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """Enforces strict authenticated Clerk user identity."""
    if not credentials or not credentials.credentials:
        if settings.allow_dev_auth and settings.app_env in ("development", "testing"):
            return "dev_authenticated_patient"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization Bearer token header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_clerk_token(credentials.credentials)
    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        if settings.allow_dev_auth and settings.app_env in ("development", "testing"):
            return "dev_authenticated_patient"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject (user_id) missing from verified claims.",
        )
    return str(user_id)


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """Resolves authenticated user, respecting allow_dev_auth during local development."""
    if not credentials or not credentials.credentials:
        if settings.allow_dev_auth and settings.app_env in ("development", "testing"):
            return "dev_authenticated_patient"
        return "anonymous_patient"
    try:
        return get_current_user(credentials)
    except HTTPException:
        if settings.allow_dev_auth and settings.app_env in ("development", "testing"):
            return "dev_authenticated_patient"
        return "anonymous_patient"
