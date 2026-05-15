from collections.abc import AsyncIterator


async def get_db_session() -> AsyncIterator[None]:
    # Placeholder dependency. SQLAlchemy session wiring will live here.
    yield None
