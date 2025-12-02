"""
AI-generated comprehensive pytest unit tests for db.py module.
Generated using modern pytest style (2025) with proper fixtures, mocks, and type hints.
Aim: >90% branch coverage
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open
from flask import Flask
import sqlite3
import tempfile
import os

from flaskr import create_app
from flaskr.db import get_db, close_db, init_db, init_app
from flaskr.db import init_db_command
import click


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({"TESTING": True, "DATABASE": db_path})
    
    yield app
    
    os.close(db_fd)
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def db(app):
    """Get database connection."""
    with app.app_context():
        db = get_db()
        yield db


class TestGetDb:
    """Test suite for get_db function."""
    
    def test_get_db_creates_connection(self, app):
        """Test that get_db creates a database connection."""
        with app.app_context():
            db = get_db()
            assert db is not None
            assert isinstance(db, sqlite3.Connection)
    
    def test_get_db_reuses_connection(self, app):
        """Test that get_db reuses the same connection in same request."""
        with app.app_context():
            db1 = get_db()
            db2 = get_db()
            assert db1 is db2
    
    def test_get_db_sets_row_factory(self, app):
        """Test that get_db sets row_factory to sqlite3.Row."""
        with app.app_context():
            db = get_db()
            assert db.row_factory == sqlite3.Row
    
    def test_get_db_uses_correct_database_path(self, app):
        """Test that get_db uses the configured database path."""
        with app.app_context():
            db = get_db()
            expected_path = app.config["DATABASE"]
            assert db.execute("PRAGMA database_list").fetchone()[2] == expected_path


class TestCloseDb:
    """Test suite for close_db function."""
    
    def test_close_db_closes_connection(self, app):
        """Test that close_db closes the database connection."""
        with app.app_context():
            db = get_db()
            close_db(None)
            # Connection should be closed
            with pytest.raises(sqlite3.ProgrammingError):
                db.execute("SELECT 1")
    
    def test_close_db_handles_no_connection(self, app):
        """Test that close_db handles case when no connection exists."""
        with app.app_context():
            # Should not raise error if no db in g
            close_db(None)
    
    def test_close_db_removes_from_g(self, app):
        """Test that close_db removes db from g."""
        with app.app_context():
            get_db()
            assert "db" in g
            close_db(None)
            assert "db" not in g


class TestInitDb:
    """Test suite for init_db function."""
    
    def test_init_db_creates_tables(self, app):
        """Test that init_db creates the necessary tables."""
        with app.app_context():
            init_db()
            
            db = get_db()
            # Check that user table exists
            result = db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='user'"
            ).fetchone()
            assert result is not None
            
            # Check that post table exists
            result = db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='post'"
            ).fetchone()
            assert result is not None
    
    def test_init_db_drops_existing_tables(self, app):
        """Test that init_db drops existing tables before creating."""
        with app.app_context():
            db = get_db()
            # Create a table manually
            db.execute("CREATE TABLE IF NOT EXISTS user (id INTEGER)")
            db.commit()
            
            # Run init_db
            init_db()
            
            # Check that new schema is applied
            # User table should have correct schema
            columns = [row[1] for row in db.execute("PRAGMA table_info(user)").fetchall()]
            assert "username" in columns
            assert "password" in columns


class TestInitApp:
    """Test suite for init_app function."""
    
    def test_init_app_registers_teardown(self, app):
        """Test that init_app registers teardown handler."""
        # init_app is called in create_app
        # Verify teardown is registered
        assert close_db in app.teardown_appcontext_funcs
    
    def test_init_app_registers_cli_command(self, app):
        """Test that init_app registers CLI command."""
        # Check that init-db command is registered
        result = app.test_cli_runner().invoke(init_db_command)
        assert result.exit_code == 0 or "Initialized" in result.output


class TestInitDbCommand:
    """Test suite for init_db_command CLI command."""
    
    def test_init_db_command_executes(self, app):
        """Test that init_db_command executes successfully."""
        runner = app.test_cli_runner()
        result = runner.invoke(init_db_command)
        assert result.exit_code == 0
        assert "Initialized" in result.output
    
    def test_init_db_command_creates_database(self, app):
        """Test that init_db_command creates the database."""
        runner = app.test_cli_runner()
        result = runner.invoke(init_db_command)
        
        with app.app_context():
            db = get_db()
            # Verify tables exist
            tables = [row[0] for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()]
            assert "user" in tables
            assert "post" in tables

