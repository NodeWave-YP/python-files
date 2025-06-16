from passlib.context import CryptContext

pass_cxt = CryptContext(schemes=["bcrypt"], deprecated="auto")

class hashed:
    @staticmethod
    def hash(password: str) -> str:
        return pass_cxt.hash(password)

    @staticmethod
    def verify(plain_password: str, hash_password: str) -> bool:
        return pass_cxt.verify(plain_password, hash_password)
