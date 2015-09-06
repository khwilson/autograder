from flask import Flask, request, render_template, redirect, url_for, flash, g
from flask.ext.login import (LoginManager, current_user, login_required,
                            login_user, logout_user,
                            confirm_login, fresh_login_required)
from werkzeug.contrib.fixers import ProxyFix

from . import app
from .models import User

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


@app.before_request
def before_request():
    g.user = current_user
