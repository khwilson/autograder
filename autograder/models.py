"""
Object models and relations for the autograder.

@author Kevin Wilson - khwilson@gmail.com
"""
import datetime
import json

from flask.ext.login import UserMixin
from sqlalchemy.types import TypeDecorator, VARCHAR
from werkzeug.security import generate_password_hash, check_password_hash

from . import db


SALT_LENGTH = 100
PW_HASH_METHOD = 'pbkdf2:sha1:1000'


class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string.

    Usage::
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

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Unicode(100))
    pw_hash = db.Column(db.String(200))
    active = db.Column(db.Boolean, default=True)

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


class Project(db.Model):

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
    project_id = db.Column(db.Integer, db.ForeignKey(Project.id))
    submission_key = db.Column(String(36))
    token_hash = db.Column(db.String(200))

    results_at = db.Column(db.DateTime, nullable=True)
    results = db.Column(JSONEncodedDict, nullable=True)

    user = db.relationship("User")
    project = db.relationship("Project")

    def __init__(self, user_id, project_id, token):
        self.submitted_at = datetime.utcnow()
        self.submission_key = uuid.uuid4()
        self.user_id = user_id
        self.project_id = project_id
        self.token_hash = generate_password_hash(token, salt_length=SALT_LENGTH,
                                                 method=PW_HASH_METHOD)
        self.results_at = None
        self.results = None

    @staticmethod
    def add_submission(user, project):
        submission_key = uuid.uuid4()
        submission = Submission(user.id, project.id)
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
