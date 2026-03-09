from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import timedelta

from . import models
from . import schemas
from . import crud
from .database import engine, get_db
from .auth import create_access_token, get_current_user, require_user
from .config import settings

# Создание таблиц
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME)

@app.post("/auth/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Регистрация нового пользователя
    if crud.get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already registered")

    db_user = crud.create_user(db, user)
    return db_user

@app.post("/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Вход и получение access токена
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/links/shorten", response_model=schemas.LinkResponse, status_code=status.HTTP_201_CREATED)
def create_short_link(
    link: schemas.LinkCreate,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    # Создание короткой ссылки (доступно всем пользователям)
    try:
        user_id = current_user.id if current_user else None
        db_link = crud.create_link(db, link, user_id)
        return db_link
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/{short_code}")
def redirect_to_original(short_code: str, db: Session = Depends(get_db)):
    # Редирект на оригинальный URL
    link = crud.get_link_by_short_code(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found or expired")

    # Обновление статистики доступа
    crud.update_link_access(db, link)

    return RedirectResponse(url=link.original_url, status_code=307)

@app.get("/links/{short_code}", response_model=schemas.LinkResponse)
def get_link_info(short_code: str, db: Session = Depends(get_db)):
    # Получение информации о ссылке
    link = crud.get_link_by_short_code(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link

@app.put("/links/{short_code}", response_model=schemas.LinkResponse)
def update_link(
    short_code: str,
    link_update: schemas.LinkUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_user)
):
    # Обновление URL ссылки (требует аутентификации)
    updated_link = crud.update_link(db, short_code, link_update, current_user.id)
    if not updated_link:
        raise HTTPException(status_code=404, detail="Link not found or unauthorized")
    return updated_link

@app.delete("/links/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_link(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_user)
):
    # Удаление ссылки (требует аутентификации)
    success = crud.delete_link(db, short_code, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Link not found or unauthorized")
    return None

@app.get("/links/{short_code}/stats", response_model=schemas.LinkStats)
def get_link_stats(short_code: str, db: Session = Depends(get_db)):
    # Получение статистики ссылки
    link = crud.get_link_by_short_code(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    return schemas.LinkStats(
        short_code=link.short_code,
        original_url=link.original_url,
        created_at=link.created_at,
        access_count=link.access_count,
        last_accessed=link.last_accessed,
        expires_at=link.expires_at
    )

@app.get("/links/search/", response_model=List[schemas.LinkResponse])
def search_links(original_url: str, db: Session = Depends(get_db)):
    # Поиск ссылок по оригинальному URL
    links = crud.search_links_by_url(db, original_url)
    return links

@app.post("/admin/cleanup/expired", status_code=status.HTTP_200_OK)
def cleanup_expired(db: Session = Depends(get_db), current_user: models.User = Depends(require_user)):
    # Очистка истекших ссылок
    crud.cleanup_expired_links(db)
    return {"message": "Expired links cleaned up"}

@app.post("/admin/cleanup/unused", status_code=status.HTTP_200_OK)
def cleanup_unused(
    days: int = settings.UNUSED_LINK_DAYS,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_user)
):
    # Очистка неиспользуемых ссылок (не использовались N дней)
    crud.cleanup_unused_links(db, days)
    return {"message": f"Unused links (>{days} days) cleaned up"}

@app.get("/admin/expired", response_model=List[schemas.ExpiredLinkResponse])
def get_expired_links_history(db: Session = Depends(get_db), current_user: models.User = Depends(require_user)):
    # Получение истории истекших ссылок
    expired_links = crud.get_expired_links(db)
    return expired_links

@app.get("/")
def root():
    # Корневой endpoint
    return {"message": "URL Shortener API", "docs": "/docs"}
