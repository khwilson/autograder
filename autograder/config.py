"""
Configuration objects and functions. The global config is stored here in the
config variable and `load_config` should be called if you want to use it.

@author Kevin Wilson - khwilson@gmail.com
"""

import yaml


config = None


class Config:
    def __init__(self, d):
        self.secret_key = d['secret_key']
        self.sqlalchemy_database_uri = d['sqlalchemy_database_uri']
        self.iron = IronConfig(d['iron'])
        self.local_config = LocalConfig(d['local']) if 'local' in d else LocalConfig.get_default()
        self.submissions_directory = d['submissions_directory']
        self.holding_directory = d['holding_directory']


class IronConfig:
    def __init__(self, d):
        self.project_id = d['project_id']


class LocalConfig:
    def __init__(self, d):
        self.payload_directory = d['payload_directory']

    @staticmethod
    def get_default():
        return LocalConfig({'payload_directory': '.'})


def load_config(f):
    """ Return a config specified in a yaml contained in f. Verify that it is valid.

    :param f: Anything yaml.load can read pointing to a config
    :return: The config
    :rtype: Config
    :raises ValueError: If any verification fails.
    """
    with open(f, 'rb') as f:
        cfg = yaml.load(f)
    global config
    config = Config(cfg)
    return config


def config_app(app, config):
    app.config['SECRET_KEY'] = config.secret_key
    app.config['SQLALCHEMY_DATABASE_URI'] = config.sqlalchemy_database_uri


def get_config():
    return config
