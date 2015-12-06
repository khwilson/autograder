"""
Queuing functions for the IronWorker framework from iron.io.

@author Kevin Wilson - khwilson@gmail.com
"""
import os
import shutil
import subprocess
import uuid

from iron_worker import IronWorker, Task

from ..utils import NamedTemporaryDirectory
from .. import models, storage


# Max timeout for now
TIMEOUT = 60


def make_worker(directory, executable, project_type, project_key):
    """
    Makes an iron.io worker and uploads it to the central repo.

    :param str directory: A dirctory which contains all the worker's dependencies
    :param str executable: The shell string which will be executed by the worker
    :param str project_type: A valid iron.io image type
    :param str project_key: The unique identifier of the project to be used on iron.io
    :raises subprocess.CalledProcessError: If something goes wrong uploading the image
    """
    with NamedTemporaryDirectory() as tmpdir:
        archive = shutil.make_archive(directory, 'zip', os.path.join(tmpdir, 'data'))
        subprocess.check_call(['iron', 'worker', 'upload', '--zip', archive,
                               '--name', project_key, 'iron/images:' + project_type, executable])


def submit_code(user, project, code):
    """ Submit code on behalf of a user on a particular project

    :param models.User user: The user
    :param models.Project project: The project
    :param str code: The code to submit. If the file is a directory, then zips it up and
        submits it. If the file is a regular file, submits as is.
    """
    with NamedTemporaryDirectory() as tmpdir:
        token = uuid.uuid4()
        submission = models.Submission(user.id, project.id, token)
        archive_name = os.path.join(tmpdir, submission.submission_key)
        if os.path.isdir(code):
            archive = shutil.make_archive(code, 'zip', archive_name)
        elif code.endswith('.zip'):
            archive = code
        else:
            shutil.copy(code, tmpdir)
            archive = shutil.make_archive(tmpdir, 'zip', archive_name)

        storage.push_archive(archive)

    payload = {
        'submission_key': submission.submission_key,
        'token': token
    }

    worker = IronWorker()
    task = Task(code_name=project.project_key, payload=payload, timeout=TIMEOUT)
    response = worker.queue(task)
    return response
