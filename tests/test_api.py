import pytest

class TestAuth:
    # Тесты эндпоинтов аутентификации

    def test_register_user(self, client):
        # Тест регистрации пользователя
        response = client.post("/auth/register", json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "password123"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert "id" in data
        assert "hashed_password" not in data

    def test_register_duplicate_username(self, client, test_user):
        # Тест регистрации с дублирующимся именем пользователя
        response = client.post("/auth/register", json={
            "username": test_user["username"],
            "email": "another@example.com",
            "password": "password123"
        })
        assert response.status_code == 400

    def test_login_success(self, client, test_user):
        # Тест успешного входа
        response = client.post("/auth/login", data={
            "username": test_user["username"],
            "password": test_user["password"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        # Тест входа с неправильным паролем
        response = client.post("/auth/login", data={
            "username": test_user["username"],
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        # Тест входа с несуществующим пользователем
        response = client.post("/auth/login", data={
            "username": "nonexistent",
            "password": "password123"
        })
        assert response.status_code == 401

class TestLinkCreation:
    # Тесты эндпоинтов создания ссылок

    def test_create_link_without_auth(self, client):
        # Тест создания ссылки без аутентификации
        response = client.post("/links/shorten", json={
            "original_url": "https://example.com"
        })
        assert response.status_code == 201
        data = response.json()
        assert "short_code" in data
        assert data["original_url"] == "https://example.com/"
        assert data["access_count"] == 0

    def test_create_link_with_auth(self, client, auth_headers):
        # Тест создания ссылки с аутентификацией
        response = client.post("/links/shorten", json={
            "original_url": "https://github.com"
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert "short_code" in data

    def test_create_link_custom_alias(self, client):
        # Тест создания ссылки с пользовательским alias
        response = client.post("/links/shorten", json={
            "original_url": "https://example.com",
            "custom_alias": "my-custom-link"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["short_code"] == "my-custom-link"

    def test_create_link_duplicate_alias(self, client):
        # Тест создания ссылки с дублирующимся alias
        client.post("/links/shorten", json={
            "original_url": "https://example.com",
            "custom_alias": "duplicate"
        })
        response = client.post("/links/shorten", json={
            "original_url": "https://another.com",
            "custom_alias": "duplicate"
        })
        assert response.status_code == 400

    def test_create_link_invalid_alias(self, client):
        # Тест создания ссылки с невалидным alias
        response = client.post("/links/shorten", json={
            "original_url": "https://example.com",
            "custom_alias": "ab"  # Too short
        })
        assert response.status_code == 400

    def test_create_link_with_expiration(self, client):
        # Тест создания ссылки с датой истечения
        response = client.post("/links/shorten", json={
            "original_url": "https://example.com",
            "expires_at": "2026-12-31T23:59:00"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["expires_at"] is not None

class TestLinkRedirect:
    # Тесты функциональности редиректа ссылок

    def test_redirect_existing_link(self, client):
        # Тест редиректа на существующую ссылку
        # Create link
        create_response = client.post("/links/shorten", json={
            "original_url": "https://example.com"
        })
        short_code = create_response.json()["short_code"]

        # Test redirect
        response = client.get(f"/{short_code}", follow_redirects=False)
        assert response.status_code == 307
        assert "example.com" in response.headers["location"]

    def test_redirect_nonexistent_link(self, client):
        # Тест редиректа на несуществующую ссылку
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_redirect_updates_stats(self, client):
        # Тест что редирект обновляет статистику доступа
        # Create link
        create_response = client.post("/links/shorten", json={
            "original_url": "https://example.com"
        })
        short_code = create_response.json()["short_code"]

        # Access link multiple times
        for _ in range(3):
            client.get(f"/{short_code}", follow_redirects=False)

        # Check stats
        stats_response = client.get(f"/links/{short_code}/stats")
        assert stats_response.status_code == 200
        data = stats_response.json()
        assert data["access_count"] == 3
        assert data["last_accessed"] is not None

class TestLinkCRUD:
    # Тесты CRUD операций со ссылками

    def test_get_link_info(self, client):
        # Тест получения информации о ссылке
        create_response = client.post("/links/shorten", json={
            "original_url": "https://example.com"
        })
        short_code = create_response.json()["short_code"]

        response = client.get(f"/links/{short_code}")
        assert response.status_code == 200
        data = response.json()
        assert data["short_code"] == short_code

    def test_update_link_with_auth(self, client, auth_headers):
        # Тест обновления ссылки с аутентификацией
        # Create link with auth
        create_response = client.post("/links/shorten", json={
            "original_url": "https://example.com"
        }, headers=auth_headers)
        short_code = create_response.json()["short_code"]

        # Update link
        response = client.put(f"/links/{short_code}", json={
            "original_url": "https://newurl.com"
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "newurl.com" in data["original_url"]

    def test_update_link_without_auth(self, client):
        # Тест обновления ссылки без аутентификации
        create_response = client.post("/links/shorten", json={
            "original_url": "https://example.com"
        })
        short_code = create_response.json()["short_code"]

        response = client.put(f"/links/{short_code}", json={
            "original_url": "https://newurl.com"
        })
        assert response.status_code == 401

    def test_delete_link_with_auth(self, client, auth_headers):
        # Тест удаления ссылки с аутентификацией
        create_response = client.post("/links/shorten", json={
            "original_url": "https://example.com"
        }, headers=auth_headers)
        short_code = create_response.json()["short_code"]

        response = client.delete(f"/links/{short_code}", headers=auth_headers)
        assert response.status_code == 204

        # Verify link is deleted
        get_response = client.get(f"/{short_code}")
        assert get_response.status_code == 404

    def test_delete_link_without_auth(self, client):
        # Тест удаления ссылки без аутентификации
        create_response = client.post("/links/shorten", json={
            "original_url": "https://example.com"
        })
        short_code = create_response.json()["short_code"]

        response = client.delete(f"/links/{short_code}")
        assert response.status_code == 401

class TestLinkStats:
    # Тесты статистики ссылок

    def test_get_stats(self, client):
        # Тест получения статистики ссылки
        create_response = client.post("/links/shorten", json={
            "original_url": "https://example.com"
        })
        short_code = create_response.json()["short_code"]

        response = client.get(f"/links/{short_code}/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["short_code"] == short_code
        assert data["original_url"] == "https://example.com/"
        assert "access_count" in data
        assert "created_at" in data

    def test_stats_nonexistent_link(self, client):
        # Тест получения статистики для несуществующей ссылки
        response = client.get("/links/nonexistent/stats")
        assert response.status_code == 404

class TestLinkSearch:
    # Тесты функциональности поиска ссылок

    def test_search_by_url(self, client):
        # Тест поиска ссылок по оригинальному URL
        url = "https://searchtest.com"

        # Create multiple links with same URL
        for _ in range(3):
            client.post("/links/shorten", json={"original_url": url})

        response = client.get(f"/links/search/?original_url={url}/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_search_no_results(self, client):
        # Тест поиска без результатов
        response = client.get("/links/search/?original_url=https://nonexistent.com")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

class TestAdminEndpoints:
    # Тесты админских эндпоинтов

    def test_cleanup_expired_with_auth(self, client, auth_headers):
        # Тест очистки истекших ссылок с аутентификацией
        response = client.post("/admin/cleanup/expired", headers=auth_headers)
        assert response.status_code == 200

    def test_cleanup_expired_without_auth(self, client):
        # Тест очистки истекших ссылок без аутентификации
        response = client.post("/admin/cleanup/expired")
        assert response.status_code == 401

    def test_cleanup_unused_with_auth(self, client, auth_headers):
        # Тест очистки неиспользуемых ссылок с аутентификацией
        response = client.post("/admin/cleanup/unused?days=30", headers=auth_headers)
        assert response.status_code == 200

    def test_get_expired_history_with_auth(self, client, auth_headers):
        # Тест получения истории истекших ссылок с аутентификацией
        response = client.get("/admin/expired", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_expired_history_without_auth(self, client):
        # Тест получения истории истекших ссылок без аутентификации
        response = client.get("/admin/expired")
        assert response.status_code == 401
