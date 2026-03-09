import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import sys
import os
from unittest.mock import MagicMock, patch

# Добавление src в path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# URL тестовой базы данных
TEST_DATABASE_URL = "sqlite:///./test.db"

# Создание тестового engine перед импортом приложения
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Мок Redis кэша
mock_cache = MagicMock()
mock_cache.get.return_value = None
mock_cache.set.return_value = True
mock_cache.delete.return_value = True

# Патчинг перед импортом
with patch('src.cache.cache', mock_cache):
    with patch('src.database.engine', test_engine):
        from src import models
        from src.database import Base, get_db
        from src.main import app

@pytest.fixture(scope="function")
def db_session():
    # Создание тестовой сессии БД
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def client(db_session):
    # Создание тестового клиента с тестовой БД
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with patch('src.crud.cache', mock_cache):
        with TestClient(app) as test_client:
            yield test_client

    app.dependency_overrides.clear()

@pytest.fixture
def test_user(client):
    # Создание тестового пользователя и возврат учетных данных
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    return user_data

@pytest.fixture
def auth_token(client, test_user):
    # Получение токена аутентификации для тестового пользователя
    response = client.post(
        "/auth/login",
        data={"username": test_user["username"], "password": test_user["password"]}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.fixture
def auth_headers(auth_token):
    # Получение заголовков авторизации
    return {"Authorization": f"Bearer {auth_token}"}
