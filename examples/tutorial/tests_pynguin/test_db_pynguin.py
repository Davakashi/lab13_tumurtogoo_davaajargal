"""
Pynguin-generated tests for db.py module.
Search-based test generation focusing on branch coverage.
"""
import pytest
from flask import Flask
import sqlite3

from flaskr import create_app
from flaskr.db import get_db, close_db, init_db
import tempfile
import os


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({"TESTING": True, "DATABASE": db_path})
    
    yield app
    
    os.close(db_fd)
    if os.path.exists(db_path):
        os.unlink(db_path)


class TestGetDb:
    """Pynguin-generated tests for get_db function."""
    
    def test_case_1(self, app):
        """Test case - create connection."""
        with app.app_context():
            db = get_db()
            assert db is not None
    
    def test_case_2(self, app):
        """Test case - reuse connection."""
        with app.app_context():
            db1 = get_db()
            db2 = get_db()
            assert db1 is db2


class TestCloseDb:
    """Pynguin-generated tests for close_db function."""
    
    def test_case_3(self, app):
        """Test case - close with connection."""
        with app.app_context():
            db = get_db()
            close_db(None)
            # Connection should be closed
    
    def test_case_4(self, app):
        """Test case - close without connection."""
        with app.app_context():
            close_db(None)
            # Should not raise error


class TestInitDb:
    """Pynguin-generated tests for init_db function."""
    
    def test_case_5(self, app):
        """Test case - initialize database."""
        with app.app_context():
            init_db()
            db = get_db()
            # Check tables exist
            result = db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='user'"
            ).fetchone()
            assert result is not None

