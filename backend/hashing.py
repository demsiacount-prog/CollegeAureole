from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    if not password or len(password) < 8:
        raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password:
        return False
    return pwd_context.verify(plain_password, hashed_password)