"""Optional token-based authentication middleware.

If SAVEMONEY_ACCESS_TOKEN is set in the environment, every request must include
an `Authorization: Bearer <token>` header.  If the variable is not set,
authentication is skipped (backward-compatible with local-only usage).
"""

import os
from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer_scheme = HTTPBearer(auto_error=False)


def get_required_token() -> Optional[str]:
    """Return the configured access token, or None if not set."""
    token = os.getenv("SAVEMONEY_ACCESS_TOKEN", "").strip()
    return token or None


async def verify_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> None:
    """FastAPI dependency that enforces the token when configured.

    Add `Depends(verify_token)` to any route (or the entire app via middleware)
    to protect it.
    """
    required = get_required_token()
    if required is None:
        return  # Auth disabled – open access

    if credentials is None or credentials.credentials != required:
        raise HTTPException(status_code=401, detail="未授权：缺少或无效的访问令牌")