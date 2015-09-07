import random
import string


TOKEN_CHARACTERS = string.ascii_letters + string.digits


def random_token(length=64):
    return ''.join(random.choice(TOKEN_CHARACTERS) for _ in range(length))
