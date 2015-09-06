import yaml


config = None


class Config(object):
    def __init__(self, d):
        self.secret_key = d['secret_key']
        self.sqlalchemy_database_uri = d['sqlalchemy_database_uri']


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
