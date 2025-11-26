import pytest
import uuid
from fastapi.testclient import TestClient

class TestBotofarmAPI:

    def test_health_check(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_create_user_success(self, client: TestClient):
        user_data = {
            "login": f"test_{uuid.uuid4()}@example.com",
            "password": "testpassword123",
            "project_id": str(uuid.uuid4()),
            "env": "stage",
            "domain": "regular"
        }

        response = client.post("/api/v1/users/", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["login"] == user_data["login"]
        assert data["env"] == user_data["env"]
        assert "password" not in data
        assert "id" in data

        return data["id"]

    def test_create_user_duplicate_email(self, client: TestClient):
        user_data = {
            "login": "duplicate@example.com",
            "password": "testpassword123",
            "project_id": str(uuid.uuid4()),
            "env": "stage",
            "domain": "regular"
        }

        response1 = client.post("/api/v1/users/", json=user_data)
        assert response1.status_code == 200

        response2 = client.post("/api/v1/users/", json=user_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]

    def test_get_users(self, client: TestClient):
        self.test_create_user_success(client)

        response = client.get("/api/v1/users/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

    def test_acquire_lock_success(self, client: TestClient):
        user_id = self.test_create_user_success(client)

        response = client.post(f"/api/v1/users/{user_id}/lock")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["message"] == "User locked successfully"
        assert data["locktime"] is not None

    def test_acquire_lock_already_locked(self, client: TestClient):
        user_id = self.test_create_user_success(client)
        client.post(f"/api/v1/users/{user_id}/lock")

        response = client.post(f"/api/v1/users/{user_id}/lock")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert data["message"] == "User already locked"

    def test_acquire_lock_user_not_found(self, client: TestClient):
        fake_user_id = "00000000-0000-0000-0000-000000000000"

        response = client.post(f"/api/v1/users/{fake_user_id}/lock")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert data["message"] == "User not found"

    def test_release_lock_success(self, client: TestClient):
        user_id = self.test_create_user_success(client)
        client.post(f"/api/v1/users/{user_id}/lock")

        response = client.post(f"/api/v1/users/{user_id}/unlock")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["message"] == "User unlocked successfully"

    def test_release_lock_user_not_found(self, client: TestClient):
        fake_user_id = "00000000-0000-0000-0000-000000000000"

        response = client.post(f"/api/v1/users/{fake_user_id}/unlock")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert data["message"] == "User not found"

    def test_lock_after_release(self, client: TestClient):
        user_id = self.test_create_user_success(client)

        lock1 = client.post(f"/api/v1/users/{user_id}/lock")
        assert lock1.json()["success"] == True

        unlock = client.post(f"/api/v1/users/{user_id}/unlock")
        assert unlock.json()["success"] == True

        lock2 = client.post(f"/api/v1/users/{user_id}/lock")
        assert lock2.json()["success"] == True

    def test_user_is_locked_method(self, client: TestClient):
        user_id = self.test_create_user_success(client)

        users_response = client.get("/api/v1/users/")
        user = next(u for u in users_response.json() if u["id"] == user_id)
        assert user["locktime"] is None

        client.post(f"/api/v1/users/{user_id}/lock")

        users_response = client.get("/api/v1/users/")
        user = next(u for u in users_response.json() if u["id"] == user_id)
        assert user["locktime"] is not None

    def test_user_validation(self, client: TestClient):
        invalid_data = {
            "login": "not-an-email",
            "password": "123",
            "project_id": "not-uuid",
            "env": "invalid-env",
            "domain": "invalid-domain"
        }

        response = client.post("/api/v1/users/", json=invalid_data)
        assert response.status_code == 422