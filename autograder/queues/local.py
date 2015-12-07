import os
import shutil
import uuid

from ..config import get_config


def make_worker(filename, executable):
    """
    Given a path to a payload and an executable to invoke, setup a
    Project which uses this payload and executable.

    :param str filename: The file containing the payload
    :param str executable: The executable to invoke
    :return: The key assigned to the project
    :rtype: str
    """
    config = get_config()
    project_key = uuid.uuid4()
    shutil.copyfile(filename, os.path.join(config.local_config.payload_directory,
                                           '{}.zip'.format(project_key)))
    return str(project_key)
