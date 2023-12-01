
# ! MAIN

DEBUG: bool = True

VERSION="0.1.0"
TITLE="DanoneMarket" 
SUMMARY="DanoneMarket private docs" 

SERVER_IP: str = "127.0.0.1"
SERVER_PORT: int = 8000

DATABASE_URL: str = "postgresql+asyncpg://..."

ALGORITHM: str = "HS256"
# openssl rand -hex 32

ACCESS_SECRET_KEY = ""
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12

REFRESH_TSECRET_KEY = ""
REFRESH_TOKEN_EXPIRE_MINUTES = 10080

EMAIL_SECRET_KEY = ""
EMAIL_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

PASSWORD_RESET_SECRET_KEY = ""
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES = 60

# ! DTO.USERS

# username validation
MIN_LENGTH_USERNAME: int = 4
MAX_LENGTH_USERNAME: int = 16
# https://regex101.com/r/GtjhIW/1
USERNAME_REGEX: str = r"^\D[а-яА-Яa-zA-Z0-9_]+$"

# password validation
MIN_LENGTH_PASSWORD: int = 7
MAX_LENGTH_PASSWORD: int = 16
# https://regex101.com/r/eUDuSY/1
PASSWORD_REGEX: str = r"^[a-zA-Z0-9!'\"№;%:?*()_+`~@#$^&-=\\><,./|]+$"


# ! UTILS MAIL

SMTP_ADRESS: str
SMTP_PORT: int
VERIFY_LOGIN: str
VERIFY_PASSWORD: str

