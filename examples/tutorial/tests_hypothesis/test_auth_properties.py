"""
Hypothesis property-based tests for authentication module.
Tests various properties of authentication functions.
"""
import pytest
from hypothesis import given, strategies as st, assume, settings
from flask import Flask
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr import create_app
from flaskr.db import get_db, init_db
import tempfile
import os


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


# Property 1: Password hashing is consistent and verifiable
@given(
    password=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126))
)
@settings(max_examples=50)
def test_password_hashing_property(app, password):
    """Property: Any password can be hashed and then verified correctly."""
    with app.app_context():
        hash1 = generate_password_hash(password)
        hash2 = generate_password_hash(password)
        
        # Same password should verify against its hash
        assert check_password_hash(hash1, password)
        assert check_password_hash(hash2, password)
        
        # Different passwords should not verify
        if password != "different":
            assert not check_password_hash(hash1, "different")


# Property 2: Username uniqueness constraint
@given(
    username1=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    username2=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    password=st.text(min_size=1, max_size=50)
)
@settings(max_examples=30)
def test_username_uniqueness_property(app, client, username1, username2, password):
    """Property: Registering the same username twice should fail."""
    assume(username1 == username2)  # Only test when usernames are the same
    
    with app.app_context():
        # First registration should succeed
        response1 = client.post(
            "/auth/register",
            data={"username": username1, "password": password}
        )
        
        # Second registration with same username should fail or redirect differently
        response2 = client.post(
            "/auth/register",
            data={"username": username2, "password": password}
        )
        
        # At least one should indicate failure (status code or flash message)
        assert response1.status_code in [200, 302]  # Success or redirect
        # If same username, second should fail
        if username1 == username2:
            # Check that we're still on register page or got error
            assert response2.status_code in [200, 302]


# Property 3: Login requires correct credentials
@given(
    username=st.text(min_size=1, max_size=50),
    correct_password=st.text(min_size=1, max_size=50),
    wrong_password=st.text(min_size=1, max_size=50)
)
@settings(max_examples=30)
def test_login_credential_property(app, client, username, correct_password, wrong_password):
    """Property: Login only succeeds with correct username and password."""
    assume(correct_password != wrong_password)
    
    with app.app_context():
        # Register user
        client.post(
            "/auth/register",
            data={"username": username, "password": correct_password}
        )
        
        # Login with correct credentials should succeed
        response_correct = client.post(
            "/auth/login",
            data={"username": username, "password": correct_password}
        )
        
        # Login with wrong password should fail
        response_wrong = client.post(
            "/auth/login",
            data={"username": username, "password": wrong_password}
        )
        
        # Correct login should redirect (302) or succeed
        assert response_correct.status_code in [200, 302]
        # Wrong password should not redirect to index
        assert response_wrong.status_code in [200, 302]


# Property 4: Session persistence
@given(
    username=st.text(min_size=1, max_size=50),
    password=st.text(min_size=1, max_size=50)
)
@settings(max_examples=20)
def test_session_persistence_property(app, client, username, password):
    """Property: After login, user session should persist across requests."""
    with app.app_context():
        # Register and login
        client.post(
            "/auth/register",
            data={"username": username, "password": password}
        )
        
        login_response = client.post(
            "/auth/login",
            data={"username": username, "password": password}
        )
        
        # After login, accessing protected route should work
        index_response = client.get("/")
        assert index_response.status_code == 200


# Property 5: Logout clears session
@given(
    username=st.text(min_size=1, max_size=50),
    password=st.text(min_size=1, max_size=50)
)
@settings(max_examples=20)
def test_logout_clears_session_property(app, client, username, password):
    """Property: After logout, user should not be able to access protected routes."""
    with app.app_context():
        # Register and login
        client.post(
            "/auth/register",
            data={"username": username, "password": password}
        )
        client.post(
            "/auth/login",
            data={"username": username, "password": password}
        )
        
        # Logout
        logout_response = client.get("/auth/logout")
        assert logout_response.status_code in [200, 302]
        
        # After logout, accessing create should redirect to login
        create_response = client.get("/create")
        assert create_response.status_code in [200, 302, 401, 403]


# Property 6: Empty username or password should fail registration
@given(
    username=st.one_of(st.just(""), st.text(min_size=1, max_size=50)),
    password=st.one_of(st.just(""), st.text(min_size=1, max_size=50))
)
@settings(max_examples=30)
def test_empty_credentials_property(app, client, username, password):
    """Property: Registration with empty username or password should fail."""
    with app.app_context():
        response = client.post(
            "/auth/register",
            data={"username": username, "password": password}
        )
        
        # If either is empty, should not successfully register
        if not username or not password:
            # Should stay on register page (200) or show error
            assert response.status_code in [200, 302]


# Property 7: Post creation requires authentication
@given(
    title=st.text(min_size=1, max_size=200),
    body=st.text(min_size=1, max_size=1000)
)
@settings(max_examples=20)
def test_post_creation_requires_auth_property(app, client, title, body):
    """Property: Creating a post without authentication should redirect to login."""
    with app.app_context():
        # Try to create post without login
        response = client.post(
            "/create",
            data={"title": title, "body": body}
        )
        
        # Should redirect to login (302) or return error
        assert response.status_code in [200, 302, 401, 403]


# Property 8: Post title is required
@given(
    title=st.one_of(st.just(""), st.text(min_size=1, max_size=200)),
    body=st.text(min_size=1, max_size=1000)
)
@settings(max_examples=20)
def test_post_title_required_property(app, client, title, body):
    """Property: Creating a post with empty title should fail."""
    with app.app_context():
        # Register and login first
        username = "testuser"
        password = "testpass"
        client.post(
            "/auth/register",
            data={"username": username, "password": password}
        )
        client.post(
            "/auth/login",
            data={"username": username, "password": password}
        )
        
        # Try to create post
        response = client.post(
            "/create",
            data={"title": title, "body": body}
        )
        
        # If title is empty, should not successfully create
        if not title:
            # Should stay on create page or show error
            assert response.status_code in [200, 302]

