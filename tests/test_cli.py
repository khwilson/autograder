from __future__ import print_function

import os
import random
import shutil
import subprocess
import tempfile
import time

import psutil
import pytest
import requests
import yaml


@pytest.fixture(scope='module')
def config_path(request):
    """ A py.test fixture which creates a config file on disk and returns the path to the config """
    submissions_directory = tempfile.mkdtemp()
    holding_directory = tempfile.mkdtemp()
    database_fd, database_filepath = tempfile.mkstemp()

    opened_file = os.fdopen(database_fd, 'w')
    opened_file.write(b'')
    opened_file.close()

    test_config = {
        'secret_key': 'itsasecret',
        'sqlalchemy_database_uri': 'sqlite:///' + database_filepath,
        'iron': {
            'project_id': 'notnecessary'
        },
        'submissions_directory': submissions_directory,
        'holding_directory': holding_directory
    }

    opened_file_descriptor, filepath = tempfile.mkstemp()
    opened_file = os.fdopen(opened_file_descriptor, 'w')
    yaml.dump(test_config, opened_file)
    opened_file.close()

    def fin():
        os.unlink(filepath)
        os.unlink(database_filepath)
        shutil.rmtree(submissions_directory)
        shutil.rmtree(holding_directory)

    request.addfinalizer(fin)
    return filepath


def term_or_kill_proc(process):
    for _ in xrange(3):
        process.terminate()
        try:
            process.wait(timeout=1)
        except psutil.TimeoutExpired:
            continue
        return
    print("Being kind didn't work; killing process {}".format(process))
    process.kill()


def terminate_proc_tree(process):
    process = psutil.Process(process.pid)
    for child in process.children(recursive=True):
        term_or_kill_proc(child)
    term_or_kill_proc(process)


@pytest.fixture(scope='module')
def db(request, config_path):
    print("Setting up database")
    subprocess.check_output(['autograder', '--config', config_path, 'db', 'setup'])


def test_db_setup(db, config_path):
    """ Just check to make sure that we don't get any errors when checking for
    tables that should be created """
    from autograder import setup_app
    setup_app(config_path)

    from autograder import models as m
    assert m.db.session.query(m.User).count() == 0


@pytest.fixture(scope='module')
def test_users(db, config_path):
    teacher_name = 'foo'
    teacher_password = 'pass'
    student_name = 'bar'
    student_password = 'word'

    subprocess.check_output(['autograder', '--config', config_path,
                             'user', 'add', teacher_name, '-p', teacher_password])
    subprocess.check_output(['autograder', '--config', config_path,
                             'user', 'add', student_name, '-p', student_password])

    return teacher_name, teacher_password, student_name, student_password


def test_user_add(db, config_path, test_users):
    teacher_name, teacher_password, student_name, student_password = test_users

    from autograder import setup_app
    setup_app(config_path)

    from autograder import models as m
    users = m.db.session.query(m.User).all()
    assert len(users) == 2
    assert {user.username for user in users} == {teacher_name, student_name}

    if users[0].username == teacher_name:
        teacher, student = users
    else:
        student, teacher = users

    assert teacher.check_password(teacher_password)
    assert not teacher.check_password(teacher_password + 'foo')
    assert student.check_password(student_password)
    assert not student.check_password(student_password + 'bar')


@pytest.fixture(scope='module')
def serve(request, config_path):
    """ Setup an autograder server

    :return: The process (from psutil) and the host and port of the server
    :rtype: psutil.Process, str, int
    """
    port = 50000 + random.randint(0, 10000)
    host = 'localhost'
    print("Spinning up web server on {host}:{port}".format(host=host, port=port))
    p = psutil.Popen(['autograder', '--config', config_path, 'web', 'start',
                      '--port', str(port), '--host', host])
    time_to_sleep = 1
    print("Sleeping for {} seconds waiting for autograder".format(time_to_sleep))
    time.sleep(time_to_sleep)

    def fin():
        print("Tearing down server at pid {}".format(p.pid))
        terminate_proc_tree(p)

    request.addfinalizer(fin)
    return p, host, port


def test_start(serve):
    _, host, port = serve
    r = requests.get("http://{host}:{port}/".format(host=host, port=port))
    assert r.ok
