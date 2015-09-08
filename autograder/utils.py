import random
import string
import uuid


TOKEN_CHARACTERS = string.ascii_letters + string.digits


def random_token(length=64):
    return ''.join(random.choice(TOKEN_CHARACTERS) for _ in range(length))


def random_project_key():
    return str(uuid.uuid4())
