import click

from sqlalchemy.orm import sessionmaker


from . import web


@click.group()
def cli():
    """ The CLI for the autograder """
    pass


@cli.group('web')
def web_group():
    """ Commands related to the web interface """
    pass


@web_group.command('start')
@click.option('--debug/--no-debug', default=False, help="Should we start the app in debug mode?")
def start(debug):
    """ Start the webserver """
    web.app.run(debug=debug)


@cli.group('user')
def user():
    """ Commands related to the user database """
    pass


@user.command('setup')
def setup_user():
    """ Setup the user database """
    from . import models
    models.create_all()


@user.command('add')
@click.argument('username')
@click.password_option()
def add_user(username, password):
    """ Add a user with the given username """
    from . import models
    models.User.add_user(username, password)
