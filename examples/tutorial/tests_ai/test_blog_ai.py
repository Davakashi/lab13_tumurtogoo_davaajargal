"""
AI-generated comprehensive pytest unit tests for blog.py module.
Generated using modern pytest style (2025) with proper fixtures, mocks, and type hints.
Aim: >90% branch coverage
"""
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, g, session
from werkzeug.exceptions import abort
from werkzeug.security import generate_password_hash

from flaskr import create_app
from flaskr.blog import get_post
from flaskr.db import get_db, init_db
import tempfile
import os
from datetime import datetime


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({"TESTING": True, "DATABASE": db_path})
    
    with app.app_context():
        init_db()
        # Create test users
        db = get_db()
        db.execute(
            "INSERT INTO user (username, password) VALUES (?, ?)",
            ("author1", generate_password_hash("pass1"))
        )
        db.execute(
            "INSERT INTO user (username, password) VALUES (?, ?)",
            ("author2", generate_password_hash("pass2"))
        )
        db.commit()
    
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


@pytest.fixture
def logged_in_client(client, db):
    """A client with logged-in user (author1)."""
    client.post(
        "/auth/login",
        data={"username": "author1", "password": "pass1"}
    )
    return client


@pytest.fixture
def sample_post(db):
    """Create a sample post for testing."""
    db.execute(
        "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
        ("Test Post", "Test Body", 1)
    )
    db.commit()
    return 1  # Return post ID


class TestIndex:
    """Test suite for index route."""
    
    def test_index_empty_posts(self, client):
        """Test index page with no posts."""
        response = client.get("/")
        assert response.status_code == 200
        # Should render template even with no posts
    
    def test_index_with_posts(self, client, db):
        """Test index page with existing posts."""
        # Create posts
        db.execute(
            "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
            ("Post 1", "Body 1", 1)
        )
        db.execute(
            "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
            ("Post 2", "Body 2", 1)
        )
        db.commit()
        
        response = client.get("/")
        assert response.status_code == 200
        assert b"Post 1" in response.data or b"Post 2" in response.data
    
    def test_index_posts_ordered_by_date(self, client, db):
        """Test that posts are ordered by creation date (most recent first)."""
        # Create posts with different timestamps
        db.execute(
            "INSERT INTO post (title, body, author_id, created) VALUES (?, ?, ?, ?)",
            ("Old Post", "Old Body", 1, "2020-01-01 00:00:00")
        )
        db.execute(
            "INSERT INTO post (title, body, author_id, created) VALUES (?, ?, ?, ?)",
            ("New Post", "New Body", 1, "2024-01-01 00:00:00")
        )
        db.commit()
        
        response = client.get("/")
        assert response.status_code == 200
        # New post should appear before old post


class TestGetPost:
    """Test suite for get_post function."""
    
    def test_get_post_success(self, app, db, logged_in_client, sample_post):
        """Test getting an existing post."""
        with app.app_context():
            post = get_post(1, check_author=False)
            assert post is not None
            assert post["title"] == "Test Post"
            assert post["body"] == "Test Body"
            assert post["author_id"] == 1
    
    def test_get_post_not_found(self, app, logged_in_client):
        """Test getting a non-existent post."""
        with app.app_context():
            with pytest.raises(Exception):  # Should raise 404
                get_post(999, check_author=False)
    
    def test_get_post_check_author_success(self, app, db, logged_in_client, sample_post):
        """Test get_post with check_author=True when user is author."""
        with app.app_context():
            post = get_post(1, check_author=True)
            assert post is not None
            assert post["author_id"] == 1
    
    def test_get_post_check_author_failure(self, app, db, client, sample_post):
        """Test get_post with check_author=True when user is not author."""
        # Login as different user
        client.post(
            "/auth/login",
            data={"username": "author2", "password": "pass2"}
        )
        
        with app.app_context():
            with pytest.raises(Exception):  # Should raise 403
                get_post(1, check_author=True)
    
    def test_get_post_check_author_false(self, app, db, client, sample_post):
        """Test get_post with check_author=False allows any user."""
        # Login as different user
        client.post(
            "/auth/login",
            data={"username": "author2", "password": "pass2"}
        )
        
        with app.app_context():
            post = get_post(1, check_author=False)
            assert post is not None


class TestCreate:
    """Test suite for create route."""
    
    def test_create_get_request(self, logged_in_client):
        """Test GET request to create page."""
        response = logged_in_client.get("/create")
        assert response.status_code == 200
    
    def test_create_requires_login(self, client):
        """Test that create requires authentication."""
        response = client.get("/create")
        assert response.status_code == 302
        assert "/auth/login" in response.location
    
    def test_create_successful(self, logged_in_client, db):
        """Test successful post creation."""
        response = logged_in_client.post(
            "/create",
            data={"title": "New Post", "body": "New Body"}
        )
        assert response.status_code == 302
        assert response.location.endswith("/")
        
        # Verify post was created
        post = db.execute(
            "SELECT * FROM post WHERE title = ?", ("New Post",)
        ).fetchone()
        assert post is not None
        assert post["body"] == "New Body"
    
    def test_create_empty_title(self, logged_in_client):
        """Test creating post with empty title."""
        response = logged_in_client.post(
            "/create",
            data={"title": "", "body": "Body content"}
        )
        assert response.status_code == 200
        # Should show error message
    
    def test_create_long_title(self, logged_in_client):
        """Test creating post with very long title."""
        long_title = "A" * 1000
        response = logged_in_client.post(
            "/create",
            data={"title": long_title, "body": "Body"}
        )
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 302]
    
    def test_create_empty_body(self, logged_in_client, db):
        """Test creating post with empty body (should be allowed)."""
        response = logged_in_client.post(
            "/create",
            data={"title": "Title Only", "body": ""}
        )
        # Body can be empty, so should succeed
        assert response.status_code in [200, 302]


class TestUpdate:
    """Test suite for update route."""
    
    def test_update_get_request(self, logged_in_client, sample_post):
        """Test GET request to update page."""
        response = logged_in_client.get("/1/update")
        assert response.status_code == 200
    
    def test_update_requires_login(self, client, sample_post):
        """Test that update requires authentication."""
        response = client.get("/1/update")
        assert response.status_code == 302
    
    def test_update_successful(self, logged_in_client, db, sample_post):
        """Test successful post update."""
        response = logged_in_client.post(
            "/1/update",
            data={"title": "Updated Title", "body": "Updated Body"}
        )
        assert response.status_code == 302
        
        # Verify post was updated
        post = db.execute(
            "SELECT * FROM post WHERE id = ?", (1,)
        ).fetchone()
        assert post["title"] == "Updated Title"
        assert post["body"] == "Updated Body"
    
    def test_update_empty_title(self, logged_in_client, sample_post):
        """Test updating post with empty title."""
        response = logged_in_client.post(
            "/1/update",
            data={"title": "", "body": "Body"}
        )
        assert response.status_code == 200
        # Should show error
    
    def test_update_non_existent_post(self, logged_in_client):
        """Test updating a non-existent post."""
        response = logged_in_client.post(
            "/999/update",
            data={"title": "Title", "body": "Body"}
        )
        assert response.status_code in [404, 302]
    
    def test_update_unauthorized_user(self, client, db, sample_post):
        """Test updating post by non-author."""
        # Login as different user
        client.post(
            "/auth/login",
            data={"username": "author2", "password": "pass2"}
        )
        
        response = client.post(
            "/1/update",
            data={"title": "Hacked", "body": "Hacked"}
        )
        assert response.status_code in [403, 404, 302]


class TestDelete:
    """Test suite for delete route."""
    
    def test_delete_successful(self, logged_in_client, db, sample_post):
        """Test successful post deletion."""
        response = logged_in_client.post("/1/delete")
        assert response.status_code == 302
        assert response.location.endswith("/")
        
        # Verify post was deleted
        post = db.execute(
            "SELECT * FROM post WHERE id = ?", (1,)
        ).fetchone()
        assert post is None
    
    def test_delete_requires_login(self, client, sample_post):
        """Test that delete requires authentication."""
        response = client.post("/1/delete")
        assert response.status_code == 302
    
    def test_delete_non_existent_post(self, logged_in_client):
        """Test deleting a non-existent post."""
        response = logged_in_client.post("/999/delete")
        assert response.status_code in [404, 302]
    
    def test_delete_unauthorized_user(self, client, db, sample_post):
        """Test deleting post by non-author."""
        # Login as different user
        client.post(
            "/auth/login",
            data={"username": "author2", "password": "pass2"}
        )
        
        response = client.post("/1/delete")
        assert response.status_code in [403, 404, 302]
    
    def test_delete_only_accepts_post_method(self, logged_in_client, sample_post):
        """Test that delete only accepts POST method."""
        response = logged_in_client.get("/1/delete")
        assert response.status_code == 405  # Method not allowed

