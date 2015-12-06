"""
Functions related to storing code and submissions.

@author Kevin Wilson - khwilson@gmail.com
"""
import shutil

from config import config


def push_archive(archive_name):
    """ Push an archive of submitted code to the appropriate place.

    :param str archive_name: The submitted code to be pushed.
    """
    shutil.copy(archive_name, config.submissions_directory)
