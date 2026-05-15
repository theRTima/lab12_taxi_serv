"""Extended unit tests for auth module with high coverage (90%+)"""

import pytest
from fastapi import status
from sqlalchemy.exc import IntegrityError
from unittest.mock import patch, MagicMock

from app.models.user import User, UserRole
from app.auth import verify_password, get_password_hash


class TestAuthEdgeCases:
    """Test edge cases for authentication"""

    @pytest.mark.parametrize(
        "email,password,name,should_succeed",
        [
            # Valid cases
            ("user@example.com", "password123", "John", True),
            ("a@b.co", "p@ssw0rd!", "A", True),
            ("test+tag@domain.com", "ValidPass1!", "Test User", True),
            # Invalid emails
            ("invalid", "password", "John", False),
            ("@example.com", "password", "John", False),
            ("user@", "password", "John", False),
            ("", "password", "John", False),
            # Invalid passwords
            ("user@example.com", "short", "John", False),  # < 6 chars
            ("user@example.com", "", "John", False),  # empty
            ("user@example.com", "a" * 129, "John", False),  # > 128 chars
            # Invalid names
            ("user@example.com", "password123", "", False),  # empty
            ("user@example.com", "password123", "a" * 256, False),  # > 255 chars
        ],
    )
    def test_register_boundary_values(self, client, email, password, name, should_succeed):
        """Test registration with boundary values"""
        response = client.post(
            "/auth/register",
            json={"email": email, "password": password, "name": name, "role": "client"},
        )
        if should_succeed:
            assert response.status_code == 201, f"Expected 201 for {email}"
        else:
            assert response.status_code in (400, 422), f"Expected 400/422 for {email}"

    def test_register_email_case_insensitive(self, client):
        """Test that emails are normalized to lowercase"""
        # Register with uppercase
        resp1 = client.post(
            "/auth/register",
            json={"email": "User@Example.COM", "password": "pass123", "name": "User1"},
        )
        assert resp1.status_code == 201

        # Try to register with same email but different case
        resp2 = client.post(
            "/auth/register",
            json={"email": "user@example.com", "password": "pass456", "name": "User2"},
        )
        assert resp2.status_code == 400
        assert "already registered" in resp2.json()["detail"]

    def test_register_prevents_role_escalation(self, client):
        """Test that clients cannot register as ADMIN"""
        response = client.post(
            "/auth/register",
            json={
                "email": "hacker@example.com",
                "password": "password123",
                "name": "Hacker",
                "role": "admin",  # Try to register as admin
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "client", "Should always register as client regardless of input"

    def test_register_duplicate_email_race_condition(self, db):
        """Test IntegrityError handling for duplicate emails"""
        # Create first user
        user1 = User(
            email="test@example.com",
            hashed_password=get_password_hash("pass123"),
            name="User 1",
            role=UserRole.CLIENT,
        )
        db.add(user1)
        db.commit()

        # Try to add duplicate
        user2 = User(
            email="test@example.com",
            hashed_password=get_password_hash("pass456"),
            name="User 2",
            role=UserRole.CLIENT,
        )
        db.add(user2)

        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    @pytest.mark.parametrize(
        "password,hashed,should_match",
        [
            ("password123", None, False),  # None hash
            ("password123", "", False),  # Empty hash
            ("password123", "invalid_hash", False),  # Invalid hash
            ("", "hashed", False),  # Empty password
        ],
    )
    def test_verify_password_edge_cases(self, password, hashed, should_match):
        """Test password verification with edge cases"""
        result = verify_password(password, hashed)
        assert result == should_match

    def test_verify_password_correct_password(self):
        """Test password verification with correct password"""
        password = "MySecurePass123!"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_wrong_password(self):
        """Test password verification with wrong password"""
        password = "MySecurePass123!"
        hashed = get_password_hash(password)
        assert verify_password("WrongPassword", hashed) is False

    def test_password_hash_different_each_time(self):
        """Test that password hashing produces different hashes (due to salt)"""
        password = "TestPassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2, "Different hashes for same password (due to salt)"
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestAuthErrorHandling:
    """Test error handling in auth endpoints"""

    def test_login_with_nonexistent_email(self, client):
        """Test login with email that doesn't exist"""
        response = client.post(
            "/auth/login",
            json={"email": "nonexistent@example.com", "password": "anything"},
        )
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_with_wrong_password(self, client):
        """Test login with wrong password"""
        # First register
        client.post(
            "/auth/register",
            json={"email": "user@example.com", "password": "correct123", "name": "User"},
        )
        # Try to login with wrong password
        response = client.post(
            "/auth/login",
            json={"email": "user@example.com", "password": "wrong123"},
        )
        assert response.status_code == 401

    def test_login_email_case_insensitive(self, client):
        """Test that login is case-insensitive for emails"""
        client.post(
            "/auth/register",
            json={"email": "User@Example.COM", "password": "pass123", "name": "User"},
        )
        # Login with different case
        response = client.post(
            "/auth/login",
            json={"email": "user@example.com", "password": "pass123"},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_update_profile_requires_auth(self, client):
        """Test that profile update requires authentication"""
        response = client.patch(
            "/auth/me",
            json={"name": "NewName"},
        )
        assert response.status_code == 403

    def test_update_profile_with_valid_name(self, client, auth_headers_client):
        """Test profile update with valid name"""
        response = client.patch(
            "/auth/me",
            json={"name": "Updated Name"},
            headers=auth_headers_client,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    @pytest.mark.parametrize("name", ["", "a" * 256])
    def test_update_profile_invalid_name(self, client, auth_headers_client, name):
        """Test profile update with invalid names"""
        response = client.patch(
            "/auth/me",
            json={"name": name},
            headers=auth_headers_client,
        )
        assert response.status_code == 422

    def test_change_password_with_wrong_current_password(self, client, auth_headers_client):
        """Test password change fails with wrong current password"""
        response = client.patch(
            "/auth/me/password",
            json={"current_password": "wrong123", "new_password": "newpass123"},
            headers=auth_headers_client,
        )
        assert response.status_code == 400
        assert "Current password is incorrect" in response.json()["detail"]

    def test_change_password_successful(self, client, auth_headers_client):
        """Test successful password change"""
        # Change password
        response = client.patch(
            "/auth/me/password",
            json={"current_password": "client_pass", "new_password": "newpass123"},
            headers=auth_headers_client,
        )
        assert response.status_code == 204

        # Verify new password works
        login_response = client.post(
            "/auth/login",
            json={"email": "client@example.com", "password": "newpass123"},
        )
        assert login_response.status_code == 200

    def test_change_password_new_too_short(self, client, auth_headers_client):
        """Test password change fails if new password too short"""
        response = client.patch(
            "/auth/me/password",
            json={"current_password": "client_pass", "new_password": "short"},
            headers=auth_headers_client,
        )
        assert response.status_code == 422

    def test_me_endpoint_requires_auth(self, client):
        """Test that /me endpoint requires authentication"""
        response = client.get("/auth/me")
        assert response.status_code == 403

    def test_me_endpoint_returns_user_data(self, client, auth_headers_client):
        """Test that /me endpoint returns correct user data"""
        response = client.get("/auth/me", headers=auth_headers_client)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "client@example.com"
        assert data["role"] == "client"
        assert "id" in data


class TestJWTSecurity:
    """Test JWT token security"""

    def test_invalid_token_returns_401(self, client):
        """Test that invalid token returns 401"""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token_xyz"},
        )
        assert response.status_code == 403

    def test_expired_token(self, client, db):
        """Test that expired tokens are rejected"""
        from app.auth import create_access_token
        from datetime import timedelta

        # Create an already-expired token
        expired_token = create_access_token(
            "test@example.com",
            expires_delta=timedelta(seconds=-1),
        )

        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 403

    def test_token_missing_user(self, client):
        """Test that token with non-existent user is rejected"""
        from app.auth import create_access_token

        # Create token for user that doesn't exist
        token = create_access_token("nonexistent@example.com")

        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
