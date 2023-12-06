from dotenv import load_dotenv
import os

# Загрузка переменных из .env файла
load_dotenv()

# MAIN

DEBUG: bool = os.getenv("DEBUG").lower() == "true"

VERSION = os.getenv("VERSION")
TITLE = os.getenv("TITLE")
SUMMARY = os.getenv("SUMMARY")

SERVER_IP: str = os.getenv("SERVER_IP")
SERVER_PORT: int = int(os.getenv("SERVER_PORT"))

DATABASE_URL: str = os.getenv("DATABASE_URL")

ALGORITHM: str = os.getenv("ALGORITHM")
ACCESS_SECRET_KEY = os.getenv("ACCESS_SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", "")
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES"))

EMAIL_SECRET_KEY = os.getenv("EMAIL_SECRET_KEY")
EMAIL_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("EMAIL_ACCESS_TOKEN_EXPIRE_MINUTES"))

PASSWORD_RESET_SECRET_KEY = os.getenv("PASSWORD_RESET_SECRET_KEY")
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES = int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES"))

# DTO.USERS

MIN_LENGTH_USERNAME: int = int(os.getenv("MIN_LENGTH_USERNAME"))
MAX_LENGTH_USERNAME: int = int(os.getenv("MAX_LENGTH_USERNAME"))
USERNAME_REGEX: str = os.getenv("USERNAME_REGEX")

MIN_LENGTH_PASSWORD: int = int(os.getenv("MIN_LENGTH_PASSWORD"))
MAX_LENGTH_PASSWORD: int = int(os.getenv("MAX_LENGTH_PASSWORD"))
PASSWORD_REGEX: str = os.getenv("PASSWORD_REGEX")

# UTILS MAIL

SMTP_ADRESS: str = os.getenv("SMTP_ADRESS")
SMTP_PORT: int = int(os.getenv("SMTP_PORT"))
VERIFY_LOGIN: str = os.getenv("VERIFY_LOGIN")
VERIFY_PASSWORD: str = os.getenv("VERIFY_PASSWORD")
