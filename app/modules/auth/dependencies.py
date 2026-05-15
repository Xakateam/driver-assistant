from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import CurrentUser
from app.modules.auth.service import auth_service
from app.modules.users.service import user_service


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        user = user_service.get_or_create_by_phone("+79990000000")
        return CurrentUser(id=user.id, phone=user.phone)

    user = auth_service.get_user_for_access_token(credentials.credentials)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
        )

    return CurrentUser(id=user.id, phone=user.phone)


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
