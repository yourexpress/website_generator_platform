"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status

from app.auth import clear_session_cookie, set_session_cookie
from app.config import settings
from app.schemas import AuthStatusResponse, LoginRequest


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthStatusResponse)
async def login(payload: LoginRequest, response: Response) -> AuthStatusResponse:
    if payload.username != settings.admin_username or payload.password != settings.admin_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    set_session_cookie(response, payload.username)
    return AuthStatusResponse(ok=True, username=payload.username)


@router.post("/logout", response_model=AuthStatusResponse)
async def logout(response: Response) -> AuthStatusResponse:
    clear_session_cookie(response)
    return AuthStatusResponse(ok=True, username=None)
