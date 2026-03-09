from locust import HttpUser, task, between
import random
import string

class URLShortenerUser(HttpUser):
    # Пользователь для нагрузочного тестирования URL shortener
    wait_time = between(1, 3)

    def on_start(self):
        # Настройка: регистрация и вход
        username = ''.join(random.choices(string.ascii_letters, k=10))
        self.user_data = {
            "username": username,
            "email": f"{username}@example.com",
            "password": "testpass123"
        }

        # Регистрация
        self.client.post("/auth/register", json=self.user_data)

        # Вход
        response = self.client.post("/auth/login", data={
            "username": self.user_data["username"],
            "password": self.user_data["password"]
        })

        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}

        self.created_links = []

    @task(5)
    def create_short_link(self):
        # Создание короткой ссылки (наиболее частая операция)
        url = f"https://example{random.randint(1, 1000)}.com/path/{random.randint(1, 100)}"
        response = self.client.post("/links/shorten", json={
            "original_url": url
        })

        if response.status_code == 201:
            self.created_links.append(response.json()["short_code"])

    @task(3)
    def redirect_to_link(self):
        # Доступ к короткой ссылке (частая операция)
        if self.created_links:
            short_code = random.choice(self.created_links)
            self.client.get(f"/{short_code}", allow_redirects=False)

    @task(2)
    def get_link_stats(self):
        # Получение статистики ссылки
        if self.created_links:
            short_code = random.choice(self.created_links)
            self.client.get(f"/links/{short_code}/stats")

    @task(1)
    def search_links(self):
        # Поиск ссылок по URL
        url = f"https://example{random.randint(1, 100)}.com/path/{random.randint(1, 10)}"
        self.client.get(f"/links/search/?original_url={url}")

    @task(1)
    def create_custom_alias(self):
        # Создание ссылки с кастомным alias
        alias = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        self.client.post("/links/shorten", json={
            "original_url": f"https://custom{random.randint(1, 1000)}.com",
            "custom_alias": alias
        })

    @task(1)
    def update_link(self):
        # Обновление ссылки (требует авторизации)
        if self.created_links and self.headers:
            short_code = random.choice(self.created_links)
            new_url = f"https://updated{random.randint(1, 1000)}.com"
            self.client.put(f"/links/{short_code}", json={
                "original_url": new_url
            }, headers=self.headers)

class AnonymousUser(HttpUser):
    # Анонимный пользователь без аутентификации
    wait_time = between(1, 2)

    def on_start(self):
        self.created_links = []

    @task(5)
    def create_short_link(self):
        # Создание короткой ссылки без авторизации
        url = f"https://anon{random.randint(1, 1000)}.com"
        response = self.client.post("/links/shorten", json={
            "original_url": url
        })

        if response.status_code == 201:
            self.created_links.append(response.json()["short_code"])

    @task(10)
    def redirect_to_link(self):
        # Доступ к коротким ссылкам
        if self.created_links:
            short_code = random.choice(self.created_links)
            self.client.get(f"/{short_code}", allow_redirects=False)
