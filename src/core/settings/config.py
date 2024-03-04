from dotenv import load_dotenv
from typing import Literal
import os

# Загрузка переменных из .env файла

current_file_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root_path = os.path.dirname(os.path.dirname(current_file_path))
env_path = os.path.join(root_path, ".env")

load_dotenv(dotenv_path=env_path, override=True)

# MAIN

DEBUG: bool = os.getenv("DEBUG").lower() == "true"
DROP_TABLES: bool = os.getenv("DROP_TABLES").lower() == "true"
ECHO_SQL: bool = os.getenv("ECHO_SQL").lower() == "true"

VERSION: str = os.getenv("VERSION")
TITLE: str = os.getenv("TITLE")
SUMMARY: str = os.getenv("SUMMARY")

SERVER_IP: str = os.getenv("SERVER_IP")
SERVER_PORT: int = int(os.getenv("SERVER_PORT"))
NGINX_DATA_ENDPOINT: str = os.getenv("NGINX_DATA_ENDPOINT")

# ATTACMENT

DATA_PATH: str = os.path.join(root_path, "data")
FILES_DELETE_MODE: str = os.getenv("FILES_DELETE_MODE")
DEFERRED_HOUR_TO_DELETE: int = int(os.getenv("DEFERRED_HOUR_TO_DELETE"))

# DATABASE

DATABASE_URL: str = os.getenv("DATABASE_URL")
REDIS_URL: str = os.getenv("REDIS_URL")

# JWT

ALGORITHM: str = os.getenv("ALGORITHM")
ACCESS_SECRET_KEY: str = os.getenv("ACCESS_SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES: float = float(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

REFRESH_SECRET_KEY: str = os.getenv("REFRESH_SECRET_KEY")
REFRESH_TOKEN_EXPIRE_MINUTES: float = float(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES"))

EMAIL_SECRET_KEY: str = os.getenv("EMAIL_SECRET_KEY")
EMAIL_ACCESS_TOKEN_EXPIRE_MINUTES: float = float(os.getenv("EMAIL_ACCESS_TOKEN_EXPIRE_MINUTES"))

PASSWORD_RESET_SECRET_KEY: str = os.getenv("PASSWORD_RESET_SECRET_KEY")
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: float = float(os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES"))

EMAIL_CHANGE_SECRET_KEY: str = os.getenv("EMAIL_CHANGE_SECRET_KEY")
EMAIL_CHANGE_TOKEN_EXPIRE_MINUTES: float = float(os.getenv("EMAIL_CHANGE_TOKEN_EXPIRE_MINUTES"))

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
SMTP_SSL_PORT: int = int(os.getenv("SMTP_SSL_PORT"))

USER_VERIFY_LOGIN: str = os.getenv("USER_VERIFY_LOGIN")
USER_VERIFY_PASSWORD: str = os.getenv("USER_VERIFY_PASSWORD")

PASSWORD_RESET_LOGIN: str = os.getenv("PASSWORD_RESET_LOGIN")
PASSWORD_RESET_PASSWORD: str = os.getenv("PASSWORD_RESET_PASSWORD")

EMAIL_CHANGE_LOGIN: str = os.getenv("EMAIL_CHANGE_LOGIN")
EMAIL_CHANGE_PASSWORD: str = os.getenv("EMAIL_CHANGE_PASSWORD")


# UTILS MARKET

BASE_ADMIN_MAIL_LOGIN: str = os.getenv("BASE_ADMIN_MAIL_LOGIN")
BASE_ADMIN_MAIL_PASSWORD: str = os.getenv("BASE_ADMIN_MAIL_PASSWORD")
BASE_ADMIN_MARKET_LOGIN: str = os.getenv("BASE_ADMIN_MARKET_LOGIN")
BASE_ADMIN_MARKET_PASSWORD: str = os.getenv("BASE_ADMIN_MARKET_PASSWORD")

# DEBUG

if DEBUG:
    BASE_DEBUG_USER_LOGIN: str = os.getenv("BASE_DEBUG_USER_LOGIN")
    BASE_DEBUG_USER_EMAIL: str = os.getenv("BASE_DEBUG_USER_EMAIL")
    BASE_DEBUG_USER_PASS: str = os.getenv("BASE_DEBUG_USER_PASS")


# LOGGING

TG_LOG_TOKEN: str = os.getenv("TG_LOG_TOKEN")
TG_ERROR_LOG_CHANNEL: int = os.getenv("TG_ERROR_LOG_CHANNEL")
TG_INFO_LOG_CHANNEL: int = os.getenv("TG_INFO_LOG_CHANNEL")
