// tests/test_main.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Gambit Chess Club API"}

# This test requires a valid admin token and a mocked Supabase client
def test_create_user_admin_only(mocker):
    # Mocking the Supabase client
    mocker.patch("app.routers.admin.supabase.auth.admin.create_user", return_value=mocker.Mock(user=mocker.Mock(id="test_uuid")))
    mocker.patch("app.routers.admin.supabase.from_", return_value=mocker.Mock(insert=mocker.Mock(return_value=mocker.Mock(execute=mocker.Mock()))))
    
    # Mocking the JWT verification to simulate an admin user
    mocker.patch("app.deps.auth.get_admin_user", return_value=mocker.Mock(role="admin"))

    new_user_data = {
        "email": "test@user.com",
        "role": "coach",
        "full_name": "Test User",
        "branch_id": "b19d5f76-8f3a-4e2b-8a71-4a1c5d0e7f9c"
    }
    
    response = client.post("/admin/users", json=new_user_data)
    
    assert response.status_code == 201
    assert "successfully" in response.json()["message"]

def test_create_user_unauthorized():
    # Mocking JWT verification to simulate a non-admin user
    mocker.patch("app.deps.auth.get_admin_user", side_effect=HTTPException(status_code=403))
    
    new_user_data = {
        "email": "unauthorized@user.com",
        "role": "coach",
        "full_name": "Unauthorized User",
        "branch_id": "b19d5f76-8f3a-4e2b-8a71-4a1c5d0e7f9c"
    }

    response = client.post("/admin/users", json=new_user_data)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not an admin"