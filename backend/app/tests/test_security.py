from datetime import timedelta
import os


def test_password_hash_is_not_plaintext_and_verifies():
    from app.core.security import hash_password, verify_password

    password = "Correct-Horse-123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_round_trip_contains_subject_and_role():
    os.environ["JWT_SECRET_KEY"] = "test-secret"

    from app.core.config import get_settings
    from app.core.security import create_access_token, decode_token

    get_settings.cache_clear()

    token = create_access_token("user-123", "customer", expires_delta=timedelta(minutes=5))
    claims = decode_token(token)

    assert claims["sub"] == "user-123"
    assert claims["role"] == "customer"
    assert claims["type"] == "access"
