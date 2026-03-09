import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils import generate_short_code, is_valid_short_code

class TestGenerateShortCode:
    # Тесты генерации короткого кода

    def test_generate_default_length(self):
        # Тест генерации короткого кода с длиной по умолчанию
        code = generate_short_code()
        assert len(code) == 6
        assert code.isalnum()

    def test_generate_custom_length(self):
        # Тест генерации короткого кода с пользовательской длиной
        code = generate_short_code(10)
        assert len(code) == 10
        assert code.isalnum()

    def test_generate_uniqueness(self):
        # Тест что сгенерированные коды различаются
        codes = [generate_short_code() for _ in range(100)]
        assert len(set(codes)) > 90  # Минимум 90% уникальных

    def test_generate_only_alphanumeric(self):
        # Тест что сгенерированные коды содержат только буквы и цифры
        for _ in range(50):
            code = generate_short_code()
            assert all(c.isalnum() for c in code)

class TestIsValidShortCode:
    # Тесты валидации короткого кода

    def test_valid_codes(self):
        # Тест валидных коротких кодов
        assert is_valid_short_code("abc123")
        assert is_valid_short_code("ABC")
        assert is_valid_short_code("123")
        assert is_valid_short_code("my-link")
        assert is_valid_short_code("my_link")
        assert is_valid_short_code("a" * 20)

    def test_invalid_too_short(self):
        # Тест кодов которые слишком короткие
        assert not is_valid_short_code("ab")
        assert not is_valid_short_code("a")
        assert not is_valid_short_code("")

    def test_invalid_too_long(self):
        # Тест кодов которые слишком длинные
        assert not is_valid_short_code("a" * 21)
        assert not is_valid_short_code("a" * 50)

    def test_invalid_characters(self):
        # Тест кодов с недопустимыми символами
        assert not is_valid_short_code("abc@123")
        assert not is_valid_short_code("abc 123")
        assert not is_valid_short_code("abc.123")
        assert not is_valid_short_code("abc/123")

    def test_none_and_empty(self):
        # Тест None и пустой строки
        assert not is_valid_short_code(None)
        assert not is_valid_short_code("")
