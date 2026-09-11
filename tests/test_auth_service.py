import uuid

from backend.services.auth_ser import AuthService


def make_service():
    return AuthService(None)


def test_access_token_roundtrip():
    service = make_service()
    user_id = uuid.uuid4()

    token = service.create_access_token(user_id)
    payload = service.decode_token(token)

    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"


def test_refresh_token_roundtrip():
    service = make_service()

    token = service.create_refresh_token(uuid.uuid4())
    payload = service.decode_token(token)

    assert payload is not None
    assert payload["type"] == "refresh"


def test_decode_invalid_token():
    service = make_service()

    assert service.decode_token("garbage.token.value") is None


def test_password_hashing_and_verify():
    service = make_service()

    hashed = service.get_password_hash("secret123")

    assert service.verify_password("secret123", hashed) is True
    assert service.verify_password("wrong-pass", hashed) is False