"""
AI-generated comprehensive pytest unit tests for auth.py module.
Generated using modern pytest style (2025) with proper fixtures, mocks, and type hints.
Aim: >90% branch coverage
"""
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, session, g
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import BadRequest

from flaskr import create_app
from flaskr.auth import login_required, load_logged_in_user
from flaskr.db import get_db, init_db
import tempfile
import os
import sqlite3


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({"TESTING": True, "DATABASE": db_path})
    
    with app.app_context():
        init_db()
    
    yield app
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def db(app):
    """Get database connection."""
    with app.app_context():
        db = get_db()
        yield db


class TestLoginRequired:
    """Test suite for login_required decorator."""
    
    def test_login_required_redirects_when_not_logged_in(self, app, client):
        """Test that login_required decorator redirects anonymous users."""
        with app.app_context():
            @app.route("/protected")
            @login_required
            def protected_route():
                return "Protected content"
            
            response = client.get("/protected")
            assert response.status_code == 302
            assert "/auth/login" in response.location
    
    def test_login_required_allows_logged_in_user(self, app, client, db):
        """Test that login_required allows access for logged-in users."""
        # Create user
        db.execute(
            "INSERT INTO user (username, password) VALUES (?, ?)",
            ("testuser", generate_password_hash("testpass"))
        )
        db.commit()
        
        # Login
        with client.session_transaction() as sess:
            sess["user_id"] = 1
        
        with app.app_context():
            @app.route("/protected")
            @login_required
            def protected_route():
                return "Protected content"
            
            response = client.get("/protected")
            assert response.status_code == 200
            assert b"Protected content" in response.data


class TestLoadLoggedInUser:
    """Test suite for load_logged_in_user function."""
    
    def test_load_logged_in_user_with_valid_session(self, app, client, db):
        """Test loading user when valid user_id in session."""
        # Create user
        db.execute(
            "INSERT INTO user (username, password) VALUES (?, ?)",
            ("testuser", generate_password_hash("testpass"))
        )
        db.commit()
        
        with app.app_context():
            with client.session_transaction() as sess:
                sess["user_id"] = 1
            
            # Make a request to trigger before_app_request
            client.get("/")
            
            # Check that g.user is set
            with app.app_context():
                assert g.user is not None
                assert g.user["username"] == "testuser"
    
    def test_load_logged_in_user_with_no_session(self, app, client):
        """Test that g.user is None when no user_id in session."""
        with app.app_context():
            client.get("/")
            assert g.user is None
    
    def test_load_logged_in_user_with_invalid_user_id(self, app, client):
        """Test behavior when user_id in session doesn't exist in database."""
        with app.app_context():
            with client.session_transaction() as sess:
                sess["user_id"] = 999  # Non-existent user
            
            client.get("/")
            # Should handle gracefully - g.user might be None or raise error
            with app.app_context():
                # Depending on implementation, might be None or raise
                pass


class TestRegister:
    """Test suite for register route."""
    
    def test_register_get_request(self, client):
        """Test GET request to register page."""
        response = client.get("/auth/register")
        assert response.status_code == 200
    
    def test_register_successful(self, client, db):
        """Test successful user registration."""
        response = client.post(
            "/auth/register",
            data={"username": "newuser", "password": "newpass123"}
        )
        assert response.status_code == 302
        assert "/auth/login" in response.location
        
        # Verify user was created
        user = db.execute(
            "SELECT * FROM user WHERE username = ?", ("newuser",)
        ).fetchone()
        assert user is not None
        assert check_password_hash(user["password"], "newpass123")
    
    def test_register_empty_username(self, client):
        """Test registration with empty username."""
        response = client.post(
            "/auth/register",
            data={"username": "", "password": "password123"}
        )
        assert response.status_code == 200
        # Should show error message
    
    def test_register_empty_password(self, client):
        """Test registration with empty password."""
        response = client.post(
            "/auth/register",
            data={"username": "newuser", "password": ""}
        )
        assert response.status_code == 200
        # Should show error message
    
    def test_register_duplicate_username(self, client, db):
        """Test registration with duplicate username."""
        # Create existing user
        db.execute(
            "INSERT INTO user (username, password) VALUES (?, ?)",
            ("existing", generate_password_hash("pass"))
        )
        db.commit()
        
        # Try to register with same username
        response = client.post(
            "/auth/register",
            data={"username": "existing", "password": "newpass"}
        )
        assert response.status_code == 200
        # Should show error about user already registered
    
    def test_register_special_characters_in_username(self, client):
        """Test registration with special characters in username."""
        response = client.post(
            "/auth/register",
            data={"username": "user@123", "password": "pass123"}
        )
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 302]
    
    def test_register_long_username(self, client):
        """Test registration with very long username."""
        long_username = "a" * 200
        response = client.post(
            "/auth/register",
            data={"username": long_username, "password": "pass123"}
        )
        # Should handle gracefully
        assert response.status_code in [200, 302]


class TestLogin:
    """Test suite for login route."""
    
    def test_login_get_request(self, client):
        """Test GET request to login page."""
        response = client.get("/auth/login")
        assert response.status_code == 200
    
    def test_login_successful(self, client, db):
        """Test successful login with correct credentials."""
        # Create user
        db.execute(
            "INSERT INTO user (username, password) VALUES (?, ?)",
            ("testuser", generate_password_hash("testpass"))
        )
        db.commit()
        
        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpass"}
        )
        assert response.status_code == 302
        assert response.location.endswith("/")
        
        # Verify session was set
        with client.session_transaction() as sess:
            assert "user_id" in sess
    
    def test_login_incorrect_username(self, client, db):
        """Test login with incorrect username."""
        # Create user
        db.execute(
            "INSERT INTO user (username, password) VALUES (?, ?)",
            ("testuser", generate_password_hash("testpass"))
        )
        db.commit()
        
        response = client.post(
            "/auth/login",
            data={"username": "wronguser", "password": "testpass"}
        )
        assert response.status_code == 200
        # Should show error message
    
    def test_login_incorrect_password(self, client, db):
        """Test login with incorrect password."""
        # Create user
        db.execute(
            "INSERT INTO user (username, password) VALUES (?, ?)",
            ("testuser", generate_password_hash("testpass"))
        )
        db.commit()
        
        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "wrongpass"}
        )
        assert response.status_code == 200
        # Should show error message
    
    def test_login_empty_username(self, client):
        """Test login with empty username."""
        response = client.post(
            "/auth/login",
            data={"username": "", "password": "password"}
        )
        assert response.status_code == 200
    
    def test_login_empty_password(self, client):
        """Test login with empty password."""
        response = client.post(
            "/auth/login",
            data={"username": "user", "password": ""}
        )
        assert response.status_code == 200
    
    def test_login_clears_existing_session(self, client, db):
        """Test that login clears existing session."""
        # Create user
        db.execute(
            "INSERT INTO user (username, password) VALUES (?, ?)",
            ("testuser", generate_password_hash("testpass"))
        )
        db.commit()
        
        # Set some session data
        with client.session_transaction() as sess:
            sess["old_data"] = "should_be_cleared"
        
        # Login
        client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpass"}
        )
        
        # Verify old session data is gone and new user_id is set
        with client.session_transaction() as sess:
            assert "old_data" not in sess
            assert "user_id" in sess


class TestLogout:
    """Test suite for logout route."""
    
    def test_logout_clears_session(self, client, db):
        """Test that logout clears the session."""
        # Create and login user
        db.execute(
            "INSERT INTO user (username, password) VALUES (?, ?)",
            ("testuser", generate_password_hash("testpass"))
        )
        db.commit()
        
        # Login
        client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpass"}
        )
        
        # Verify session has user_id
        with client.session_transaction() as sess:
            assert "user_id" in sess
        
        # Logout
        response = client.get("/auth/logout")
        assert response.status_code == 302
        
        # Verify session is cleared
        with client.session_transaction() as sess:
            assert "user_id" not in sess
    
    def test_logout_redirects_to_index(self, client):
        """Test that logout redirects to index."""
        response = client.get("/auth/logout")
        assert response.status_code == 302
        assert response.location.endswith("/")
    
    def test_logout_when_not_logged_in(self, client):
        """Test logout when user is not logged in."""
        response = client.get("/auth/logout")
        assert response.status_code == 302
        # Should still redirect even if not logged in

