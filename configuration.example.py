
# ! MAIN

DEBUG: bool = True

VERSION="0.1.0"
TITLE="DanoneMarket" 
SUMMARY="DanoneMarket private docs" 

SERVER_IP: str = "127.0.0.1"
SERVER_PORT: int = 8000

DATABASE_URL: str = "postgresql+asyncpg://username:pass@localhost:5432/dbname"

ALGORITHM: str = "HS256"
# openssl rand -hex 32
SECRET_KEY = ""
ACCESS_TOKEN_EXPIRE_MINUTES = 5


# ! DTO.USERS

# username validation
MIN_LENGTH_USERNAME: int = 3
MAX_LENGTH_USERNAME: int = 10
# https://regex101.com/r/GtjhIW/1
USERNAME_REGEX: str = r"^[a-zA-Z0-9_]+$"

# password validation
MIN_LENGTH_PASSWORD: int = 7


