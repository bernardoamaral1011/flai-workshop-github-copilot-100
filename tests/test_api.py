"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    # Save original state
    original_activities = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for name, details in original_activities.items():
        if name in activities:
            activities[name]["participants"] = details["participants"].copy()


def test_root_redirect(client):
    """Test that root redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    
    # Check that we have activities
    assert len(data) > 0
    assert "Soccer Team" in data
    assert "Basketball Club" in data
    
    # Check structure of an activity
    soccer = data["Soccer Team"]
    assert "description" in soccer
    assert "schedule" in soccer
    assert "max_participants" in soccer
    assert "participants" in soccer
    assert isinstance(soccer["participants"], list)


def test_signup_for_activity_success(client):
    """Test successful signup for an activity"""
    email = "test@mergington.edu"
    activity = "Soccer Team"
    
    response = client.post(f"/activities/{activity}/signup?email={email}")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    
    # Verify the participant was added
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert email in activities_data[activity]["participants"]


def test_signup_for_nonexistent_activity(client):
    """Test signup for an activity that doesn't exist"""
    email = "test@mergington.edu"
    activity = "Nonexistent Activity"
    
    response = client.post(f"/activities/{activity}/signup?email={email}")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_signup_duplicate(client):
    """Test that a student cannot sign up twice for the same activity"""
    email = "lucas@mergington.edu"  # Already in Soccer Team
    activity = "Soccer Team"
    
    response = client.post(f"/activities/{activity}/signup?email={email}")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "already signed up" in data["detail"].lower()


def test_unregister_success(client):
    """Test successful unregistration from an activity"""
    email = "lucas@mergington.edu"  # Already in Soccer Team
    activity = "Soccer Team"
    
    response = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    
    # Verify the participant was removed
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert email not in activities_data[activity]["participants"]


def test_unregister_from_nonexistent_activity(client):
    """Test unregister from an activity that doesn't exist"""
    email = "test@mergington.edu"
    activity = "Nonexistent Activity"
    
    response = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_unregister_not_signed_up(client):
    """Test unregister when student is not signed up"""
    email = "notsignedup@mergington.edu"
    activity = "Soccer Team"
    
    response = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "not signed up" in data["detail"].lower()


def test_signup_and_unregister_workflow(client):
    """Test complete workflow of signup and unregister"""
    email = "workflow@mergington.edu"
    activity = "Drama Club"
    
    # Get initial participant count
    initial_response = client.get("/activities")
    initial_count = len(initial_response.json()[activity]["participants"])
    
    # Sign up
    signup_response = client.post(f"/activities/{activity}/signup?email={email}")
    assert signup_response.status_code == 200
    
    # Verify participant count increased
    after_signup = client.get("/activities")
    after_signup_count = len(after_signup.json()[activity]["participants"])
    assert after_signup_count == initial_count + 1
    assert email in after_signup.json()[activity]["participants"]
    
    # Unregister
    unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert unregister_response.status_code == 200
    
    # Verify participant count returned to initial
    after_unregister = client.get("/activities")
    after_unregister_count = len(after_unregister.json()[activity]["participants"])
    assert after_unregister_count == initial_count
    assert email not in after_unregister.json()[activity]["participants"]


def test_multiple_activities_signup(client):
    """Test that a student can sign up for multiple different activities"""
    email = "multitask@mergington.edu"
    activities_list = ["Soccer Team", "Drama Club", "Chess Club"]
    
    for activity in activities_list:
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
    
    # Verify student is in all activities
    all_activities = client.get("/activities").json()
    for activity in activities_list:
        assert email in all_activities[activity]["participants"]
