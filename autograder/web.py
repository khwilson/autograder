"""
The actual Flask app to be used as the web broker for the autograder.

@author Kevin Wilson - khwilson@gmail.com
"""
import datetime
import os
import uuid

from flask import Flask, request, render_template, redirect, url_for, flash, g
from flask.ext.login import (LoginManager, current_user, login_required,
                            login_user, logout_user,
                            confirm_login, fresh_login_required)
from werkzeug.contrib.fixers import ProxyFix

from . import app, db
from .models import Project, Submission, User

app.wsgi_app = ProxyFix(app.wsgi_app)

login_manager = LoginManager()

login_manager.login_view = "login"
login_manager.login_message = u"Please log in to access this page."
login_manager.refresh_view = "reauth"

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.id == user_id).first()


login_manager.setup_app(app)

@app.route("/")
def index():
    return app.send_static_file('html/index.html')


@app.route("/secret")
@fresh_login_required
def secret():
    return "SECRET!!!!!"


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST" and "username" in request.form:
        username = request.form["username"]
        user = User.query.filter(User.username == username).first()
        if user:
            remember = request.form.get("remember", "no") == "yes"
            if login_user(user, remember=remember):
                flash("Logged in!")
                return redirect(request.args.get("next") or url_for("index"))
            else:
                flash("Sorry, but you could not log in.")
        else:
            flash(u"Invalid username.")
    return render_template('login.html')


@app.route("/reauth", methods=["GET", "POST"])
@login_required
def reauth():
    if request.method == "POST":
        confirm_login()
        flash(u"Reauthenticated.")
        return redirect(request.args.get("next") or url_for("index"))
    return "REAUTH!!!!!!!!!!"


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.")
    return redirect(url_for("index"))


class SavedZipFile(object):
    def __init__(self, file, directory):
        self.filename = os.path.join(directory, uuid.uuid4() + '.zip')
        file.save(self.filename)
    def __enter__(self):
        return self.filename
    def __exit__(self, *args):
        os.unlink(self.filename)


@app.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_project():
    if request.method == 'POST':
        project_name = request.form['project_name']
        project = Project.get_project_by_name(project_name)
        if not project:
            return render_template('submit', error="Project {} does not exist".format(project_name))
        file = request.files['file']
        if file and file.filename.endswith('.zip'):
            with SavedZipFile(file, config.holding_directory) as some_filename:
                queues.submit_code(g.user, project, some_filename)
            return "Success"
    return render_template('submit')


@app.route('/worker/code', methods=['GET'])
def worker_get_code():
    submission_key = request.args.get('submission_key')
    token = request.args.get('token')
    if not (submission_key and token):
        return "Both the submission_key and token must be set in the request", 400
    submission = Submission.get_submission_by_key(submission_key)
    if not (submission and submission.check_token(token)):
        return "Error finding submission you want to post results on", 404
    return app.send_from_directory(config.submissions_directory, submission_key + '.zip')


@app.route('/worker/results', methods=['POST'])
def worker_post_results():
    content = request.get_json()
    submission = Submission.get_submission_by_key(content['submission_key'])
    if not (submission and submission.check_token(content['token'])):
        return "Error finding submission you want to post results on", 404
    submission.results = content['results']
    submission.results_at = datetime.utcnow()
    db.session.commit()
    return "Submission results accepted", 200


@app.before_request
def before_request():
    g.user = current_user
