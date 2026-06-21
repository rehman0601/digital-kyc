import os
import unittest
import pytest
from app import app, db, User, Document, Verification, perform_aws_ocr_and_rekognition

@pytest.fixture
def client():
    # Setup test configuration
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["WTF_CSRF_ENABLED"] = False
    
    with app.app_context():
        db.create_all()
        # Seed test admin
        admin = User(
            username="testadmin",
            email="testadmin@kyc.local",
            password="pbkdf2:sha256:somehash",
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()
        
        yield app.test_client()
        
        db.session.remove()
        db.drop_all()

def test_health_endpoint(client):
    """Test that the health endpoint returns a successful JSON status."""
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "ok"

def test_home_redirect_to_login(client):
    """Test that visiting the root index redirects to the login screen."""
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

def test_user_registration(client):
    """Test registering a new user is successful and writes to the database."""
    response = client.post("/register", data={
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "password123"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(username="newuser").first()
        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.role == "user"

def test_user_login(client):
    """Test user login authentication flows."""
    # Register first
    client.post("/register", data={
        "username": "loginuser",
        "email": "loginuser@example.com",
        "password": "password123"
    })
    
    # Successful login
    response = client.post("/login", data={
        "username": "loginuser",
        "password": "password123"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Dashboard" in response.data or b"Logout" in response.data

    # Failed login
    response_fail = client.post("/login", data={
        "username": "loginuser",
        "password": "wrongpassword"
    }, follow_redirects=True)
    assert b"Invalid username or password" in response_fail.data

def test_ocr_simulation():
    """Test the AWS OCR and face recognition mock logic returns descriptive text."""
    remarks = perform_aws_ocr_and_rekognition("dummy/path.jpg", "Aadhaar", "testuser")
    assert "Aadhaar" in remarks
    assert "testuser" in remarks.lower()

    remarks_pan = perform_aws_ocr_and_rekognition("dummy/path.jpg", "PAN", "testuser")
    assert "PAN" in remarks_pan
    assert "Permanent Account Number" in remarks_pan

    remarks_passport = perform_aws_ocr_and_rekognition("dummy/path.jpg", "Passport", "testuser")
    assert "Passport" in remarks_passport
    assert "Facematch Confidence" in remarks_passport
