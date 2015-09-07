"""
Object models and relations for the autograder.

@author Kevin Wilson - khwilson@gmail.com
"""
from datetime import datetime, timedelta
import json

from flask.ext.login import UserMixin
from sqlalchemy.types import TypeDecorator, VARCHAR
from werkzeug.security import generate_password_hash, check_password_hash

from . import db
from .utils import random_token


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

    registrations = db.relationship("Registration", backref="user")

    def __init__(self, username, password, active=True):
        self.username = username
        self.pw_hash = generate_password_hash(password, salt_length=SALT_LENGTH,
                                              method=PW_HASH_METHOD)
        self.active = active

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

    def __init__(self, description, creator_id):
        self.description = description
        self.creator_id = creator_id
        self.created_at = datetime.utcnow()

    @staticmethod
    def add_unit(description, creator):
        unit = Unit(description, creator.id)
        db.session.add(unit)
        db.session.commit()
        return unit


class Registration(db.Model):
    """ This model represents a user/unit pair """

    __tablename__ = 'registrations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    unit_id = db.Column(db.Integer, db.ForeignKey(Unit.id))
    is_teacher = db.Column(db.Boolean, default=False)

    @staticmethod
    def add_registration(user, unit, is_teacher=False):
        """ Create a new registration of a user in a unit.

        :param User user: The user to create the registration for
        :param Unit unit: The unit in which to place the registration
        :param bool is_teacher: Is this registration a teacher?
        :return: The registration object committed to the db
        :rtype: Registration
        """
        reg = Registration(user.id, unit.id, is_teacher)
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


class Project(db.Model):
    """ A model representing a project that can be assigned to a unit """

    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    project_type = db.Column(db.String(100))
    project_key = db.Column(db.String(36))

    @staticmethod
    def add_project(name, project_type, project_key):
        project = Project(name, project_type, project_key)
        db.session.add(project)
        db.session.commit()
        return project

    @staticmethod
    def get_project_by_name(name):
        return db.session.query(Project).filter(Project.name == name).first()


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

    def __init__(self, user_id, assignment_id, token=None):
        if token is None:
            token = random_token()

        self.submitted_at = datetime.utcnow()
        self.submission_key = uuid.uuid4()
        self.user_id = user_id
        self.assigner_id = assignment_id
        self.token_hash = generate_password_hash(token, salt_length=SALT_LENGTH,
                                                        method=PW_HASH_METHOD)
        self.results_at = None
        self.results = None

    @staticmethod
    def add_submission(user, assignment, token=None):
        submission = Submission(user.id, project.id, token=token)
        db.session.add(submission)
        db.session.commit()
        return submission

    def check_token(self, token):
        return check_password_hash(self.token_hash, token)

    def post_results(self, results):
        self.results_at = datetime.utcnow()
        self.results = results
        db.session.commit()


def create_all():
    db.create_all()
