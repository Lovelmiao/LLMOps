import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()  # 自动生成盐
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed.encode("utf-8")
    )

password = hash_password("163110300154xK.")
print(password)
print(check_password("163110300154xK.",password))
