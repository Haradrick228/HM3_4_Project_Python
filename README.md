# URL Shortener API

Сервис для сокращения URL с аутентификацией, кэшированием и статистикой.

## Требования

- Python 3.11+
- Docker и Docker Compose
- PostgreSQL
- Redis

## Запуск приложения

### Docker 

```bash
# Запуск всех сервисов (app, PostgreSQL, Redis)
docker-compose up -d

# Приложение доступно на http://localhost:8000
# Документация API: http://localhost:8000/docs
```

## Тестирование

### Запуск всех тестов

```bash
# Все тесты с покрытием
pytest tests/ -v --cov=src --cov-report=html

# Только unit тесты
pytest tests/test_utils.py tests/test_cache.py -v

# Только функциональные тесты
pytest tests/test_api.py tests/test_edge_cases.py -v
```

### Нагрузочное тестирование

```bash
# Запуск Locust
locust -f tests/locustfile.py

# Открыть http://localhost:8089
# Указать количество пользователей и URL приложения
```

## Пример использования
```bash
# Регистрация
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"user","email":"user@example.com","password":"pass123"}'

# Создание короткой ссылки
curl -X POST http://localhost:8000/links/shorten \
  -H "Content-Type: application/json" \
  -d '{"original_url":"https://example.com"}'

# Получение статистики
curl http://localhost:8000/links/abc123/stats
```

## Покрытие тестами

- Всего тестов: 57
- Покрытие кода: 97%
- Unit тесты: 19
- Функциональные тесты: 38
