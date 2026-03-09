import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

class TestCRUDEdgeCases:
    def test_create_link_collision_resolution(self, client):
        # Тест что коллизия короткого кода разрешается
        urls = [f"https://example{i}.com" for i in range(10)]
        short_codes = []

        for url in urls:
            response = client.post("/links/shorten", json={"original_url": url})
            assert response.status_code == 201
            short_codes.append(response.json()["short_code"])

        assert len(set(short_codes)) == len(short_codes)

    def test_expired_link_cleanup(self, client, auth_headers):
        # Тест очистки истекших ссылок
        past_time = (datetime.utcnow() - timedelta(days=1)).isoformat()
        response = client.post("/links/shorten", json={
            "original_url": "https://expired.com",
            "expires_at": past_time
        }, headers=auth_headers)
        assert response.status_code == 201
        short_code = response.json()["short_code"]

        # Try to access expired link
        response = client.get(f"/{short_code}")
        assert response.status_code == 404

    def test_update_link_unauthorized_user(self, client, auth_headers):
        # Тест обновления ссылки созданной другим пользователем
        client.post("/auth/register", json={
            "username": "user2",
            "email": "user2@example.com",
            "password": "pass123"
        })
        login_response = client.post("/auth/login", data={
            "username": "user2",
            "password": "pass123"
        })
        user2_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

        create_response = client.post("/links/shorten", json={
            "original_url": "https://example.com"
        }, headers=auth_headers)
        short_code = create_response.json()["short_code"]

        response = client.put(f"/links/{short_code}", json={
            "original_url": "https://hacked.com"
        }, headers=user2_headers)
        assert response.status_code == 404

    def test_delete_link_unauthorized_user(self, client, auth_headers):
        # Тест удаления ссылки созданной другим пользователем
        client.post("/auth/register", json={
            "username": "user3",
            "email": "user3@example.com",
            "password": "pass123"
        })
        login_response = client.post("/auth/login", data={
            "username": "user3",
            "password": "pass123"
        })
        user3_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

        create_response = client.post("/links/shorten", json={
            "original_url": "https://example.com"
        }, headers=auth_headers)
        short_code = create_response.json()["short_code"]

        response = client.delete(f"/links/{short_code}", headers=user3_headers)
        assert response.status_code == 404

    def test_search_multiple_links_same_url(self, client):
        # Тест что поиск возвращает все ссылки для одного URL
        url = "https://duplicate.com"

        for i in range(5):
            client.post("/links/shorten", json={
                "original_url": url,
                "custom_alias": f"dup{i}"
            })

        response = client.get(f"/links/search/?original_url={url}/")
        assert response.status_code == 200
        assert len(response.json()) == 5

    def test_root_endpoint(self, client):
        # Тест что корневой эндпоинт возвращает правильное сообщение
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data

class TestAuthEdgeCases:
    # Тесты граничных случаев аутентификации

    def test_register_invalid_email(self, client):
        # Тест регистрации с невалидным email
        response = client.post("/auth/register", json={
            "username": "testuser",
            "email": "invalid-email",
            "password": "pass123"
        })
        assert response.status_code == 422

    def test_login_empty_credentials(self, client):
        # Тест входа с пустыми учетными данными
        response = client.post("/auth/login", data={
            "username": "",
            "password": ""
        })
        assert response.status_code == 422 or response.status_code == 401

    def test_protected_endpoint_invalid_token(self, client):
        # Тест защищенного эндпоинта с невалидным токеном
        response = client.delete("/links/test", headers={
            "Authorization": "Bearer invalid_token"
        })
        assert response.status_code == 401

    def test_protected_endpoint_no_token(self, client):
        # Тест защищенного эндпоинта без токена
        response = client.delete("/links/test")
        assert response.status_code == 401
