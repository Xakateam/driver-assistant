from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.modules.auth.dependencies import CurrentUserDep, bearer_scheme
from app.modules.auth.schemas import (
    AccessTokenOut,
    RefreshTokenIn,
    RequestCodeIn,
    RequestCodeOut,
    TokenPairOut,
    VerifyCodeIn,
)
from app.modules.auth.service import auth_service

router = APIRouter()


@router.post("/request-code", response_model=RequestCodeOut)
async def request_code(payload: RequestCodeIn) -> RequestCodeOut:
    demo_code = auth_service.request_code(payload.phone)
    return RequestCodeOut(
        message="OTP code generated",
        phone=payload.phone,
        demo_code=demo_code,
    )


@router.post("/verify-code", response_model=TokenPairOut)
async def verify_code(payload: VerifyCodeIn) -> TokenPairOut:
    token_pair = auth_service.verify_code(payload.phone, payload.code)
    if token_pair is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code",
        )

    return TokenPairOut(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
    )


@router.post("/refresh", response_model=AccessTokenOut)
async def refresh_token(payload: RefreshTokenIn) -> AccessTokenOut:
    access_token = auth_service.refresh_access_token(payload.refresh_token)
    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    return AccessTokenOut(access_token=access_token)


@router.post("/logout")
async def logout(
    current_user: CurrentUserDep,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict[str, str]:
    _ = current_user
    auth_service.revoke_access_token(credentials.credentials)
    return {"status": "ok"}
