from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from typing import Optional, List
from . import models
from . import schemas
from .utils import generate_short_code, is_valid_short_code
from .auth import get_password_hash, verify_password
from .cache import cache

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    # Создание нового пользователя
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    # Получение пользователя по имени
    return db.query(models.User).filter(models.User.username == username).first()

def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    # Аутентификация пользователя
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def create_link(db: Session, link: schemas.LinkCreate, user_id: Optional[int] = None) -> models.Link:
    # Создание новой короткой ссылки
    # Генерация или валидация короткого кода
    if link.custom_alias:
        if not is_valid_short_code(link.custom_alias):
            raise ValueError("Invalid custom alias format")
        short_code = link.custom_alias
        custom_alias = True
    else:
        short_code = generate_short_code()
        custom_alias = False

    # Проверка уникальности
    while db.query(models.Link).filter(models.Link.short_code == short_code).first():
        if custom_alias:
            raise ValueError("Custom alias already exists")
        short_code = generate_short_code()

    db_link = models.Link(
        short_code=short_code,
        original_url=str(link.original_url),
        custom_alias=custom_alias,
        expires_at=link.expires_at,
        user_id=user_id
    )
    db.add(db_link)
    db.commit()
    db.refresh(db_link)

    # Кэширование ссылки
    cache.set(f"link:{short_code}", {
        "original_url": db_link.original_url,
        "expires_at": db_link.expires_at.isoformat() if db_link.expires_at else None
    })

    return db_link

def get_link_by_short_code(db: Session, short_code: str) -> Optional[models.Link]:
    # Получение ссылки по короткому коду
    cached = cache.get(f"link:{short_code}")
    if cached:
        link = db.query(models.Link).filter(models.Link.short_code == short_code).first()
        if link:
            return link

    # Запрос к базе данных
    link = db.query(models.Link).filter(
        and_(
            models.Link.short_code == short_code,
            models.Link.is_active == True
        )
    ).first()

    if link:
        # Проверка истечения срока
        if link.expires_at and link.expires_at < datetime.utcnow():
            move_to_expired(db, link)
            return None

        # Кэширование
        cache.set(f"link:{short_code}", {
            "original_url": link.original_url,
            "expires_at": link.expires_at.isoformat() if link.expires_at else None
        })

    return link

def update_link_access(db: Session, link: models.Link):
    # Обновление статистики доступа к ссылке
    link.access_count += 1
    link.last_accessed = datetime.utcnow()
    db.commit()

    # Обновление кэша
    cache.set(f"link:{link.short_code}", {
        "original_url": link.original_url,
        "expires_at": link.expires_at.isoformat() if link.expires_at else None
    })

def update_link(db: Session, short_code: str, link_update: schemas.LinkUpdate, user_id: int) -> Optional[models.Link]:
    # Обновление URL ссылки
    link = db.query(models.Link).filter(
        and_(
            models.Link.short_code == short_code,
            models.Link.user_id == user_id
        )
    ).first()

    if not link:
        return None

    link.original_url = str(link_update.original_url)
    db.commit()
    db.refresh(link)

    # Инвалидация кэша
    cache.delete(f"link:{short_code}")

    return link

def delete_link(db: Session, short_code: str, user_id: int) -> bool:
    # Удаление ссылки
    link = db.query(models.Link).filter(
        and_(
            models.Link.short_code == short_code,
            models.Link.user_id == user_id
        )
    ).first()

    if not link:
        return False

    db.delete(link)
    db.commit()

    # Инвалидация кэша
    cache.delete(f"link:{short_code}")

    return True

def search_links_by_url(db: Session, original_url: str) -> List[models.Link]:
    # Поиск ссылок по оригинальному URL
    return db.query(models.Link).filter(
        and_(
            models.Link.original_url == original_url,
            models.Link.is_active == True
        )
    ).all()

def move_to_expired(db: Session, link: models.Link):
    # Перемещение ссылки в таблицу истекших
    expired = models.ExpiredLink(
        short_code=link.short_code,
        original_url=link.original_url,
        created_at=link.created_at,
        total_accesses=link.access_count,
        user_id=link.user_id
    )
    db.add(expired)
    db.delete(link)
    db.commit()

    # Инвалидация кэша
    cache.delete(f"link:{link.short_code}")

def cleanup_expired_links(db: Session):
    # Очистка истекших ссылок
    now = datetime.utcnow()
    expired_links = db.query(models.Link).filter(
        and_(
            models.Link.expires_at != None,
            models.Link.expires_at < now
        )
    ).all()

    for link in expired_links:
        move_to_expired(db, link)

def cleanup_unused_links(db: Session, days: int):
    # Очистка неиспользуемых ссылок
    threshold = datetime.utcnow() - timedelta(days=days)
    unused_links = db.query(models.Link).filter(
        and_(
            models.Link.last_accessed != None,
            models.Link.last_accessed < threshold
        )
    ).all()

    for link in unused_links:
        move_to_expired(db, link)

def get_expired_links(db: Session) -> List[models.ExpiredLink]:
    # Получение всех истекших ссылок
    return db.query(models.ExpiredLink).order_by(models.ExpiredLink.expired_at.desc()).all()
