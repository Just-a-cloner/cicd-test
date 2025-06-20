import pytest
import os
import tempfile
from app import create_app
from config import TestConfig
from models import db

@pytest.fixture(scope='session')
def app():
    """Create application for the tests."""
    # Create a temporary file to serve as the test database
    db_fd, db_path = tempfile.mkstemp()
    
    class TestingConfig(TestConfig):
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    
    app = create_app(TestingConfig)
    
    with app.app_context():
        db.create_all()
    
    yield app
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test runner for the app's Click commands."""
    return app.test_cli_runner()

# Removed autouse clean_db fixture to avoid conflicts with test class fixtures