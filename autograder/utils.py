"""
Utilities for general use in the project.

@author Kevin Wilson - khwilson@gmail.com
"""

import random
import shutil
import string
import tempfile
import uuid


TOKEN_CHARACTERS = string.ascii_letters + string.digits


class NamedTemporaryDirectory(object):
    """
    A context manager that creates a temporary directory and deletes
    it on exit

    >>> with NamedTemporaryDirectory() as directory:
    ...     assert os.path.isdir(directory)
    ...     with open(os.path.join(directory, 'somefile'), 'w') as f:
    ...         f.write("HELLO!!!!")
    ... assert not os.path.exists(os.path.join(directory, 'somefile'))
    ... assert not os.path.exists(directory)
    """

    def __init__(self):
        self.directory = tempfile.mkdtemp()

    def __enter__(self):
        return self.directory

    def __exit__(self, *args):
        shutil.rmtree(self.directory)


def random_token(length=64):
    """ Return a token to be used later for authentication.

    Characters in the token are chosen from `TOKEN_CHARACTERS` and
    then length of the token is a function argument.

    :param int length: The length of the token to create.
    :return: The token
    :rtype: str
    """
    return ''.join(random.choice(TOKEN_CHARACTERS) for _ in range(length))


def random_project_key():
    """ Return a random key for a project.

    Currently implemented as a stringy u-u-i-d version 4.

    :return: A random project key
    :rtype: str
    """
    return str(uuid.uuid4())
