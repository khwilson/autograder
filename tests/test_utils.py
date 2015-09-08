import os
import random

from autograder import utils


def test_named_temporary_directory():
    """
    Create a directory, add a file, and exit the `with`.

    No errors should arise and the file and directory should be gone
    after exiting the `with`.
    """
    with utils.NamedTemporaryDirectory() as directory:
        assert os.path.isdir(directory)
        with open(os.path.join(directory, 'somefile'), 'w') as f:
            f.write("HELLO!!!!")
    assert not os.path.exists(os.path.join(directory, 'somefile'))
    assert not os.path.exists(directory)


def test_random_token():
    """
    Test that utils.random_token returns tokens of the specified length
    and that they aren't all the same.
    """
    # Set the seed so that we have determinism
    random.seed(0)
    tokens = [utils.random_token(length=length) for length in range(1, 20)]
    for i, token in enumerate(tokens):
        assert len(token) == i + 1, (("Should have been length {} "
            "but was length {}").format(i+1, len(token)))

    # Make sure that tokens are actually somewhat random
    for i in range(len(tokens) - 1):
        assert tokens[i] != tokens[i+1][:i+1]


def test_random_project_key():
    """ Just make sure the each project key is different """
    keys = [utils.random_project_key() for _ in range(20)]
    assert len(set(keys)) == len(keys)
