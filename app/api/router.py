from fastapi import APIRouter

from app.api.v1 import (
    admin,
    auth,
    balance,
    dashboard,
    debts,
    feed,
    ml,
    notifications,
    recommendations,
    trips,
    users,
    vehicles,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(vehicles.router, prefix="/vehicles", tags=["Vehicles"])
api_router.include_router(trips.router, prefix="/trips", tags=["Trips"])
api_router.include_router(balance.router, prefix="/balance", tags=["Balance"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(debts.router, prefix="/debts", tags=["Debts"])
api_router.include_router(feed.router, prefix="/feed", tags=["Feed"])
api_router.include_router(
    notifications.router,
    prefix="/notifications",
    tags=["Notifications"],
)
api_router.include_router(
    recommendations.router,
    prefix="/recommendations",
    tags=["Recommendations"],
)
api_router.include_router(ml.router, prefix="/ml", tags=["ML"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])


@api_router.get("/version", tags=["Health"])
async def version() -> dict[str, str]:
    return {"api": "v1"}
