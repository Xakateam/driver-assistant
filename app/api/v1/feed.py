from fastapi import APIRouter, Query

from app.api.deps import CurrentUserDep
from app.modules.feed.service import get_feed as build_feed

router = APIRouter()


@router.get("")
async def get_feed(
    current_user: CurrentUserDep,
    type: str = Query(default="all", pattern="^(all|trips|payments|overdues)$"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, object]:
    return build_feed(
        user_id=current_user.id,
        kind=type,
        limit=limit,
        offset=offset,
    )
