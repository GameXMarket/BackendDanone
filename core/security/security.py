from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Медленная функция хеширования, для защиты от атак по времени


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str, salt: str = None) -> str:
    if salt:  # Не имеет особого смысла, соль автоматически генерируется
        password = password + salt
    return pwd_context.hash(password)
