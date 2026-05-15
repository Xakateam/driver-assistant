from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUserDep
from app.modules.recommendations.service import recommendation_service

router = APIRouter()


@router.get("")
async def get_recommendations(current_user: CurrentUserDep) -> list[dict[str, object]]:
    return recommendation_service.list_recommendations(user_id=current_user.id)


@router.post("/{recommendation_id}/accept")
async def accept_recommendation(
    recommendation_id: str,
    current_user: CurrentUserDep,
) -> dict[str, object]:
    recommendation = recommendation_service.accept(
        user_id=current_user.id,
        recommendation_id=recommendation_id,
    )
    if recommendation is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return recommendation


@router.post("/{recommendation_id}/decline")
async def decline_recommendation(
    recommendation_id: str,
    current_user: CurrentUserDep,
) -> dict[str, object]:
    recommendation = recommendation_service.decline(
        user_id=current_user.id,
        recommendation_id=recommendation_id,
    )
    if recommendation is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return recommendation
