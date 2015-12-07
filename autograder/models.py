"""
Object models and relations for the autograder.

@author Kevin Wilson - khwilson@gmail.com
"""
from datetime import datetime, timedelta
import json
import uuid

from flask.ext.login import UserMixin
from sqlalchemy.types import TypeDecorator, VARCHAR
from werkzeug.security import generate_password_hash, check_password_hash

from . import db
from .utils import random_project_key, random_token


SALT_LENGTH = 100
PW_HASH_METHOD = 'pbkdf2:sha1:1000'

ONE_YEAR = timedelta(365)


class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string.

    Ganked from the SQLAlchemy docs. To use, specify a string length, just like
    for a VARCHAR, e.g.::
        JSONEncodedDict(255)
    """

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class User(db.Model, UserMixin):
    """ A model representing a user """

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Unicode(100))
    pw_hash = db.Column(db.String(200))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime)

    registrations = db.relationship("Registration", backref="user")

    def __init__(self, username, password, active=True):
        self.username = username
        self.pw_hash = generate_password_hash(password, salt_length=SALT_LENGTH,
                                              method=PW_HASH_METHOD)
        self.active = active
        self.created_at = datetime.utcnow()

    def is_active(self):
        return self.active

    def check_password(self, password):
        return check_password_hash(self.pw_hash, password)

    @staticmethod
    def add_user(username, password):
        user = User(username, password)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def get_user_by_name(username):
        return db.session.query(User).filter(User.username == username).first()


class Teacher(db.Model):
    """ This model represents all the users who have teacher powers in a class """
    __tablename__ = 'teachers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    unit_id = db.Column(db.Integer, db.ForeignKey("units.id"))

    @staticmethod
    def add_teacher(user, unit):
        """ Add a teacher to a unit

        :param User user: The user who should be a teacher
        :param Unit unit: The unit to which they will be added as a teacher
        :return: The Teacher object
        :rtype: Teacher
        """
        teacher = Teacher(user_id=user.id, unit_id=unit.id)
        db.session.add(teacher)
        db.session.commit()
        return teacher


class Unit(db.Model):
    """ This model represents a class, but we can't call it a class because reserved words """
    __tablename__ = 'units'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255))
    creator_id = db.Column(db.Integer, db.ForeignKey(User.id))
    created_at = db.Column(db.DateTime)

    registrations = db.relationship("Registration", backref="unit")
    assignments = db.relationship("Assignment", backref="unit")
    creator = db.relationship("User")
    teachers = db.relationship("Teacher", backref="unit")

    def __init__(self, description, creator_id):
        self.description = description
        self.creator_id = creator_id
        self.created_at = datetime.utcnow()

    @staticmethod
    def add_unit(description, creator):
        """ Create a unit with the passed description and creator.

        :param str description: A description of the course
        :param User creator: The person creating the course.
        :return: The created Unit
        :rtype: Unit
        """
        unit = Unit(description, creator.id)
        db.session.add(unit)
        db.session.commit()

        # When a unit is created, make sure to setup its creator as a teacher
        teacher = Teacher(user_id=creator.id, unit_id=unit.id)
        db.session.add(teacher)
        db.session.commit()

        return unit


class Registration(db.Model):
    """ This model represents a user/unit pair """

    __tablename__ = 'registrations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    unit_id = db.Column(db.Integer, db.ForeignKey(Unit.id))

    @staticmethod
    def add_registration(user, unit):
        """ Create a new registration of a user in a unit.

        :param User user: The user to create the registration for
        :param Unit unit: The unit in which to place the registration
        :param bool is_teacher: Is this registration a teacher?
        :return: The registration object committed to the db
        :rtype: Registration
        """
        reg = Registration(user_id=user.id, unit_id=unit.id)
        db.session.add(reg)
        db.session.commit()
        return reg


class Assignment(db.Model):
    """ A model which represents a project/unit pair """

    __tablename__ = 'assignments'

    id = db.Column(db.Integer, primary_key=True)
    due_date = db.Column(db.DateTime)
    unit_id = db.Column(db.Integer, db.ForeignKey(Unit.id))
    assigner_id = db.Column(db.Integer, db.ForeignKey(User.id))
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"))

    assigner = db.relationship("User")
    project = db.relationship("Project")

    def __init__(self, assigner_id, unit_id, project_id, due_date=None, max_submissions=-1):
        """ Initailize an assignment.

        :param int assigner_id: Who is assigning the assignment? Should be a teacher
            in the relevant unit at the time of assignment.
        :param int unit_id: The unit which this assignment is associated with.
        :param int project_id: Which project is being assigned?
        :param datetime due_date: When is the assignment due? If not specified, then
            it will be due 1 year hence.
        :param int max_submissions: The maximum number of submissions allowed. If -1,
            then an infinite number is allowed.
        """
        self.assigner_id = assigner_id
        self.unit_id = unit_id
        self.project_id = project_id
        self.due_date = due_date or datetime.utcnow() + ONE_YEAR
        self.max_submissions = max_submissions

    @staticmethod
    def add_assignment(assigner, unit, project, due_date=None, max_submissions=-1):
        """
        :param int assigner_id: Who is assigning the assignment? Should be a teacher
            in the relevant unit at the time of assignment.
        :param int unit_id: The unit which this assignment is associated with.
        :param int project_id: Which project is being assigned?
        :param datetime due_date: When is the assignment due? If not specified, then
            it will be due 1 year hence.
        :param int max_submissions: The maximum number of submissions allowed. If -1,
            then an infinite number is allowed.
        :return: The created assignment
        :rtype: Assignment
        :raises ValueError: If the assigner is not a teacher in the passed unit
        """
        if not any(teacher.id == assigner.id for teacher in unit.teachers):
            raise ValueError("Only a teacher may assign a project to a unit")
        assignment = Assignment(assigner.id, unit.id, project.id,
                                due_date=due_date, max_submissions=max_submissions)
        db.session.add(assignment)
        db.session.commit()
        return assignment


class Project(db.Model):
    """ A model representing a project that can be assigned to a unit """

    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    executable = db.Column(db.String(255))
    project_key = db.Column(db.String(36))
    created_at = db.Column(db.DateTime)
    creator_id = db.Column(db.Integer, db.ForeignKey(User.id))

    creator = db.relationship("User")

    def __init__(self, name, executable, creator_id, project_key):
        self.name = name
        self.executable = executable
        self.project_key = project_key
        self.creator_id = creator_id
        self.created_at = datetime.utcnow()

    @staticmethod
    def add_project(name, executable, creator, project_key=None):
        project_key = project_key or random_project_key()
        project = Project(name=name, executable=executable,
                          creator_id=creator.id, project_key=project_key)
        db.session.add(project)
        db.session.commit()
        return project

    @staticmethod
    def get_project_by_name(name):
        return db.session.query(Project).filter(Project.name == name).first()

    @staticmethod
    def get_project_by_key(project_key):
        return db.session.query(Project).filter(Project.project_key == project_key).first()


class Submission(db.Model):

    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    submitted_at = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    assignment_id = db.Column(db.Integer, db.ForeignKey(Assignment.id))
    submission_key = db.Column(db.String(36))
    token_hash = db.Column(db.String(200))

    results_at = db.Column(db.DateTime, nullable=True)
    results = db.Column(JSONEncodedDict(65535), nullable=True)

    user = db.relationship("User")
    assignment = db.relationship("Assignment")

    def __init__(self, user_id, assignment_id, token):
        self.submitted_at = datetime.utcnow()
        self.submission_key = str(uuid.uuid4())
        self.user_id = user_id
        self.assignment_id = assignment_id
        self.token_hash = generate_password_hash(token, salt_length=SALT_LENGTH,
                                                 method=PW_HASH_METHOD)
        self.results_at = None
        self.results = None

    @staticmethod
    def add_submission(user, assignment, token=None):
        """ Add a submission. Note that every submission needs a token so that the
        autograder can post results. If you do not supply a token, then a random one
        will be generated.

        :param User user: The user submitting
        :param Assignment assignment: The assignment the user is submitting
        :param str|None token: The token used to submit results of the submission
        :return: The Submission object and token
        :rtype: Submission, str
        :raises ValueError: If the user has not been assigned the given assignment
        """
        if not token:
            token = random_token()

        if (len(user.registrations) == 0 or
                not any(assignment.unit_id == reg.unit_id for reg in user.registrations)):
            raise ValueError("A user may only submit an assignment they've been assigned")

        submission = Submission(user.id, assignment.id, token=token)
        db.session.add(submission)
        db.session.commit()
        return submission, token

    def check_token(self, token):
        return check_password_hash(self.token_hash, token)

    def post_results(self, results):
        self.results_at = datetime.utcnow()
        self.results = results
        db.session.commit()


def create_all():
    db.create_all()


def drop_all():
    db.drop_all()
