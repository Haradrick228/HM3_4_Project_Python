from setuptools import setup, find_packages

setup(
    name="url-shortener",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.109.0",
        "uvicorn[standard]==0.27.0",
        "sqlalchemy==2.0.25",
        "psycopg2-binary==2.9.9",
        "redis==5.0.1",
        "pydantic==2.5.3",
        "pydantic-settings==2.1.0",
        "email-validator==2.1.0",
        "python-jose[cryptography]==3.3.0",
        "passlib==1.7.4",
        "bcrypt==4.0.1",
        "python-multipart==0.0.6",
    ],
)
