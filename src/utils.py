import random
import string
from .config import settings

def generate_short_code(length: int = None) -> str:
    # Генерация случайного короткого кода для URL
    if length is None:
        length = settings.SHORT_CODE_LENGTH

    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def is_valid_short_code(code: str) -> bool:
    # Валидация формата короткого кода
    if not code or len(code) < 3 or len(code) > 20:
        return False
    return all(c in string.ascii_letters + string.digits + '-_' for c in code)
