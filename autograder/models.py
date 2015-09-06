from flask.ext.login import UserMixin

from werkzeug.security import generate_password_hash, check_password_hash

from . import db


SALT_LENGTH = 100
PW_HASH_METHOD = 'pbkdf2:sha1:1000'


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
        db.session.add(User(username, password))
        db.session.commit()


def create_all():
    db.create_all()
