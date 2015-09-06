from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from . import config as config_module


app = Flask(__name__, static_url_path='')
config = None
db = SQLAlchemy(app)


def setup_app(config_path):
    global config
    cfg = config_module.load_config(config_path)
    config_module.config_app(app, cfg)
    config = config_module.config
