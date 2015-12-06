from datetime import datetime, timedelta

import os
import shutil
import tempfile

import pytest
import yaml

from sqlalchemy.orm import load_only

import autograder


@pytest.fixture(scope='module')
def config_path(request):
    """ A py.test fixture which creates a config file on disk and returns the path to the config """
    submissions_directory = tempfile.mkdtemp()
    holding_directory = tempfile.mkdtemp()

    test_config = {
        'secret_key': 'itsasecret',
        'sqlalchemy_database_uri': 'sqlite://',
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
        shutil.rmtree(submissions_directory)
        shutil.rmtree(holding_directory)

    request.addfinalizer(fin)
    return filepath


@pytest.fixture(scope='module')
def models(config_path):
    """ Setup the sqlite db and initialize the models """
    autograder.setup_app(config_path)

    # Now that setup has occurred, we can import the models
    from autograder import models as m
    m.create_all()
    return m


def test_models(models):
    # Insert a few users
    users = []
    for suffix in '12345':
        username = u'username' + suffix
        password = 'password' + suffix
        models.User.add_user(username, password)
        user = models.User.get_user_by_name(username)
        users.append(user)
        assert user is not None, "User {} was not stored in db".format(username)
        assert user.check_password(password), "Password was not set correctly"
        assert not user.check_password(password + 'nope'), \
            "Password check succeeded when it shouldn't"
    assert models.db.session.query(models.User).count() == 5

    # Max tolerance allowed for db to create the unit entry
    create_time_tolerance = timedelta(seconds=10)

    # Insert a few units
    units = []
    for creator, suffix in zip(users, '12345'):
        description = 'Class ' + suffix
        now = datetime.utcnow()
        unit = models.Unit.add_unit(description, creator)
        units.append(unit)
        assert unit.created_at - now < create_time_tolerance
        assert unit.creator.username == creator.username

    # Make sure that the creator of the unit is a teacher
    for unit in units:
        teachers = models.db.session.query(models.Teacher).filter(
            models.Teacher.unit_id == unit.id).all()
        assert len(teachers) == 1
        teacher = teachers[0]
        assert teacher.id == unit.creator_id

    assert models.db.session.query(models.Unit).count() == 5

    # Add a student (Rotate the users by one for student)
    registrations = []
    for unit, student in zip(units, users[1:] + [users[0]]):
        reg = models.Registration.add_registration(student, unit)
        registrations.append(reg)
        assert reg.user.id == student.id
        assert reg.unit.id == unit.id

    assert models.db.session.query(models.Registration).count() == 5

    # Make a few projects
    projects = []
    for user, suffix in zip(users, '12345'):
        project_name = 'project' + suffix
        project_type = 'type' + suffix
        project = models.Project.add_project(project_name, project_type, user)
        projects.append(project)
        assert project.creator.id == user.id
        assert project.creator_id == user.id

    assert models.db.session.query(models.Project).count() == 5
    db_projects = models.db.session.query(models.Project).options(load_only("project_key")).all()
    assert ({project.project_key for project in db_projects} ==
            {project.project_key for project in projects})

    # Make a few assignments
    assignments = []
    for i, (user, unit, project) in enumerate(zip(users, units, projects)):
        assignment = models.Assignment.add_assignment(user, unit, project, max_submissions=i)
        assignments.append(assignment)
        assert assignment.unit.id == unit.id
        assert assignment.project.id == project.id
        assert assignment.assigner.id == user.id
        assert datetime.utcnow() - assignment.due_date < create_time_tolerance + models.ONE_YEAR
        assert assignment.max_submissions == i

    assert models.db.session.query(models.Assignment).count() == 5

    # Try to have a non-teacher create an assignment
    with pytest.raises(ValueError):
        models.Assignment.add_assignment(users[1], units[0], projects[2])

    # Make a few submissions (Note that we have to rotate the users so they'll be students)
    submissions = []
    for user, assignment in zip(users[1:] + [users[0]], assignments):
        submission, token = models.Submission.add_submission(user, assignment)
        submissions.append(submission)
        assert submission.user.id == user.id
        assert submission.assignment.id == assignment.id
        assert submission.check_token(token)
        assert not submission.check_token(token + 'foo')

    assert len({submission.submission_key for submission in submissions}) == 5
    assert models.db.session.query(models.Submission).count() == 5

    # Post some results
    for submission, result in zip(submissions, 'ABCDF'):
        submission.post_results({'grade': result})

    assert {submission.results['grade'] for submission in models.db.session.query(models.Submission).options(load_only("results")).all()} == \
            set('ABCDF')
