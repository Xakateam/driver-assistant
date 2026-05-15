from secrets import token_urlsafe


def create_demo_token() -> str:
    return token_urlsafe(32)
