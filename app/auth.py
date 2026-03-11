from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from app import db, mail
from app.models import User
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("main.dashboard"))

        flash("Fel användarnamn eller lösenord")

    return render_template("login.html", show_navbar=False)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        password = request.form.get("password")

        existing = User.query.filter_by(email=email).first()

        if existing:
            flash("Användarnamn eller e-post finns redan")
            return redirect(url_for("auth.register"))

        # 🔥 Skicka till databasen
        user = User(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            password_hash=generate_password_hash(password)
        )

        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Konto skapat!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("register.html", show_navbar=False)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@auth_bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()

        if user:
            token = user.generate_reset_token()
            send_reset_email(user.email, token)

        flash("Om kontot finns har mail skickats.")
        return redirect(url_for("auth.login"))

    return render_template("forgot_password.html", show_navbar=False)


def send_reset_email(email, token):
    reset_url = url_for("auth.reset_password", token=token, _external=True)

    msg = Message(
        "VaccApp Password Reset",
        sender="noreply@vaccapp.com",
        recipients=[email],
    )

    msg.body = f"""
Återställ ditt lösenord:

{reset_url}

Om du inte begärde detta kan du ignorera mailet.
"""

    mail.send(msg)


@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.verify_reset_token(token)

    if not user:
        flash("Token ogiltig eller har gått ut.")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password")
        user.set_password(password)
        db.session.commit()

        flash("Lösenord uppdaterat.")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", show_navbar=False)