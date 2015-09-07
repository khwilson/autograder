import random

from autograder import utils


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
