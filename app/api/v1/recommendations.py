from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CurrentUserDep
from app.api.v1.schemas import RecommendationOut
from app.modules.recommendations.service import recommendation_service

router = APIRouter()


@router.get("", response_model=list[RecommendationOut])
async def get_recommendations(
    current_user: CurrentUserDep,
    include_decided: bool = Query(default=False),
) -> list[RecommendationOut]:
    return recommendation_service.list_recommendations(
        user_id=current_user.id,
        include_decided=include_decided,
    )


@router.post("/{recommendation_id}/accept", response_model=RecommendationOut)
async def accept_recommendation(
    recommendation_id: str,
    current_user: CurrentUserDep,
) -> RecommendationOut:
    recommendation = recommendation_service.accept(
        user_id=current_user.id,
        recommendation_id=recommendation_id,
    )
    if recommendation is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return recommendation


@router.post("/{recommendation_id}/decline", response_model=RecommendationOut)
async def decline_recommendation(
    recommendation_id: str,
    current_user: CurrentUserDep,
) -> RecommendationOut:
    recommendation = recommendation_service.decline(
        user_id=current_user.id,
        recommendation_id=recommendation_id,
    )
    if recommendation is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return recommendation
