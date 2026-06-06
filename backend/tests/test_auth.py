import pytest
from backend.app.services.auth_service import hash_password, verify_password, create_access_token
import uuid

def test_password_hashing():
    pw = "test-password-123"
    hashed = hash_password(pw)
    assert verify_password(pw, hashed)
    assert not verify_password("wrong", hashed)

def test_access_token_contains_company_id():
    from jose import jwt
    user_id = uuid.uuid4()
    company_id = uuid.uuid4()
    token = create_access_token(user_id, company_id, "owner")
    payload = jwt.decode(token, options={"verify_signature": False})
    assert payload["company_id"] == str(company_id)
    assert payload["sub"] == str(user_id)
    assert payload["role"] == "owner"
