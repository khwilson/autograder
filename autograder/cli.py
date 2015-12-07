"""
The command line interface for the autograder.

@author Kevin Wilson - khwilson@gmail.com
"""
import getpass
import sys

import click

from . import setup_app, web
from .queues import local as queues


@click.group()
@click.option('--config', '-c', nargs=1, help="Location of config yaml")
@click.pass_context
def cli(ctx, config):
    """ The CLI for the autograder """
    setup_app(config)


@cli.group('web')
def web_group():
    """ Commands related to the web interface """
    pass


@web_group.command('start')
@click.option('--port', '-p', nargs=1, type=int, default=8888)
@click.option('--host', '-h', nargs=1, type=str, default='localhost')
@click.option('--debug/--no-debug', default=False, help="Should we start the app in debug mode?")
def start(debug, host, port):
    """ Start the webserver """
    web.app.run(debug=debug, host=host, port=port)


@cli.group('user')
def user():
    """ Commands related to the user database """
    pass


@user.command('add')
@click.argument('username')
@click.option('--password', '-p', nargs=1, default=None,
              help="Specify a password on the command line. If not passed, then "
                   "user will be prompted for a password.")
@click.password_option()
def add_user(username, password):
    """ Add a user with the given username """
    if not password:
        password = getpass.getpass()

    from . import models
    models.User.add_user(username, password)


@cli.group('project')
def project():
    """ Commands related to projects """
    pass


@project.command('add')
@click.argument('username')
@click.argument('name')
@click.argument('payload')
@click.argument('executable')
@click.option('--password', '-p', nargs=1, type=str, default=None)
def add_project(username, name, payload, executable, password):
    from . import models
    attempts = 0
    user = models.db.session.query(models.User).filter(models.User.username == username).first()
    while not user.check_password(password or '') and attempts < 3:
        password = getpass.getpass()
        if password and user.check_password(password):
            break
        attempts += 1

    if attempts == 3:
        raise ValueError("Too many attempts at password")

    project_key = queues.make_worker(payload, executable)
    models.Project.add_project(name, executable, user, project_key=project_key)
    click.echo("Project added with key {}".format(project_key))


@cli.group('submissions')
def submit_group():
    pass


@submit_group.command('submit')
@click.argument('username')
@click.argument('project_name')
@click.argument('code_directory')
@click.password_option
def submit_code(username, project_name, code_directory, password):
    from . import models, queues
    user = models.User.get_user_by_name(username)
    if not user:
        click.echo("User {} doesn't exist".format(username), err=True)
        sys.exit(1)

    if not user.check_password(password):
        click.echo("Incorrect password for user {}".format(username), err=True)
        sys.exit(1)

    project = models.Project.get_project_by_name(project_name)
    if not project:
        click.echo("Project {} does not exist".format(project_name), err=True)
        sys.exit(1)

    submission = queues.submit_code(user, project, code_directory)
    models.db.session.add(submission)
    models.db.commit()


@cli.group('db')
def db():
    pass


@db.command('setup')
@click.option('--recreate/--keep',
              help="Recreate the entire database or merely insert missing tables",
              default=False)
def setup_db(recreate):
    from autograder import models as m
    if recreate:
        m.drop_all()
    m.create_all()


def main():
    return cli(obj={})
