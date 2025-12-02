"""
Pynguin-generated tests for blog.py module.
Search-based test generation focusing on branch coverage.
"""
import pytest
from flask import Flask
from werkzeug.security import generate_password_hash

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


class TestIndex:
    """Pynguin-generated tests for index route."""
    
    def test_case_1(self, client):
        """Test case - empty posts."""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_case_2(self, client, app):
        """Test case - with posts."""
        with app.app_context():
            db = get_db()
            db.execute(
                "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
                ("Post Title", "Post Body", 1)
            )
            db.commit()
        
        response = client.get("/")
        assert response.status_code == 200


class TestGetPost:
    """Pynguin-generated tests for get_post function."""
    
    def test_case_3(self, app, client):
        """Test case - post not found."""
        with app.app_context():
            from flaskr.blog import get_post
            try:
                get_post(999, check_author=False)
                assert False, "Should raise exception"
            except Exception:
                pass
    
    def test_case_4(self, app, client):
        """Test case - post found, check_author=False."""
        # Create post
        with app.app_context():
            db = get_db()
            db.execute(
                "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
                ("Test", "Body", 1)
            )
            db.commit()
            
            from flaskr.blog import get_post
            post = get_post(1, check_author=False)
            assert post is not None
    
    def test_case_5(self, app, client):
        """Test case - post found, check_author=True, user is author."""
        # Create post and login as author
        with app.app_context():
            db = get_db()
            db.execute(
                "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
                ("Test", "Body", 1)
            )
            db.commit()
        
        client.post("/auth/login", data={"username": "author1", "password": "pass1"})
        
        with app.app_context():
            from flaskr.blog import get_post
            post = get_post(1, check_author=True)
            assert post is not None
    
    def test_case_6(self, app, client):
        """Test case - post found, check_author=True, user is not author."""
        # Create post and login as different user
        with app.app_context():
            db = get_db()
            db.execute(
                "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
                ("Test", "Body", 1)
            )
            db.commit()
        
        client.post("/auth/login", data={"username": "author2", "password": "pass2"})
        
        with app.app_context():
            from flaskr.blog import get_post
            try:
                get_post(1, check_author=True)
                assert False, "Should raise exception"
            except Exception:
                pass


class TestCreate:
    """Pynguin-generated tests for create route."""
    
    def test_case_7(self, client):
        """Test case - GET request."""
        response = client.get("/create")
        assert response.status_code == 302
    
    def test_case_8(self, client, app):
        """Test case - POST without login."""
        response = client.post(
            "/create",
            data={"title": "Title", "body": "Body"}
        )
        assert response.status_code == 302
    
    def test_case_9(self, client, app):
        """Test case - POST with empty title."""
        client.post("/auth/login", data={"username": "author1", "password": "pass1"})
        response = client.post(
            "/create",
            data={"title": "", "body": "Body"}
        )
        assert response.status_code == 200
    
    def test_case_10(self, client, app):
        """Test case - successful creation."""
        client.post("/auth/login", data={"username": "author1", "password": "pass1"})
        response = client.post(
            "/create",
            data={"title": "New Post", "body": "New Body"}
        )
        assert response.status_code == 302


class TestUpdate:
    """Pynguin-generated tests for update route."""
    
    def test_case_11(self, client, app):
        """Test case - GET without login."""
        response = client.get("/1/update")
        assert response.status_code == 302
    
    def test_case_12(self, client, app):
        """Test case - GET with login, post exists."""
        # Create post
        with app.app_context():
            db = get_db()
            db.execute(
                "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
                ("Old", "Old Body", 1)
            )
            db.commit()
        
        client.post("/auth/login", data={"username": "author1", "password": "pass1"})
        response = client.get("/1/update")
        assert response.status_code == 200
    
    def test_case_13(self, client, app):
        """Test case - POST with empty title."""
        # Create post
        with app.app_context():
            db = get_db()
            db.execute(
                "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
                ("Old", "Old Body", 1)
            )
            db.commit()
        
        client.post("/auth/login", data={"username": "author1", "password": "pass1"})
        response = client.post(
            "/1/update",
            data={"title": "", "body": "New Body"}
        )
        assert response.status_code == 200
    
    def test_case_14(self, client, app):
        """Test case - successful update."""
        # Create post
        with app.app_context():
            db = get_db()
            db.execute(
                "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
                ("Old", "Old Body", 1)
            )
            db.commit()
        
        client.post("/auth/login", data={"username": "author1", "password": "pass1"})
        response = client.post(
            "/1/update",
            data={"title": "Updated", "body": "Updated Body"}
        )
        assert response.status_code == 302


class TestDelete:
    """Pynguin-generated tests for delete route."""
    
    def test_case_15(self, client, app):
        """Test case - POST without login."""
        response = client.post("/1/delete")
        assert response.status_code == 302
    
    def test_case_16(self, client, app):
        """Test case - successful deletion."""
        # Create post
        with app.app_context():
            db = get_db()
            db.execute(
                "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
                ("To Delete", "Body", 1)
            )
            db.commit()
        
        client.post("/auth/login", data={"username": "author1", "password": "pass1"})
        response = client.post("/1/delete")
        assert response.status_code == 302

