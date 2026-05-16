from fastapi import APIRouter

from app.modules.auth.dependencies import CurrentUserDep
from app.modules.users.schemas import UserOut
from app.modules.users.service import user_service

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_me(current_user: CurrentUserDep) -> UserOut:
    user = user_service.get_by_id(current_user.id)
    if user is None:
        return UserOut(id=current_user.id, phone=current_user.phone)
    return UserOut(**user.__dict__)
