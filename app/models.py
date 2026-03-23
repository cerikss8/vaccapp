from . import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from datetime import datetime, date
from sqlalchemy import case


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(120), unique=True, nullable=False)

    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    phone = db.Column(db.String(20))

    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    # NYTT: User -> Persons
    persons = db.relationship("Person", backref="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self):
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        return s.dumps(self.id, salt="password-reset")

    @staticmethod
    def verify_reset_token(token, expires_sec=3600):
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        try:
            user_id = s.loads(token, salt="password-reset", max_age=expires_sec)
        except:
            return None
        return User.query.get(user_id)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80))
    date_of_birth = db.Column(db.Date)
    relationship = db.Column(db.String(20), default="child")  # self / child / other

    vaccinations = db.relationship("Vaccination", backref="person", cascade="all, delete-orphan")

class Dose(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dose_number = db.Column(db.Integer, nullable=False)
    date_taken = db.Column(db.Date, nullable=True)
    comment = db.Column(db.Text)
    provider = db.Column(db.String(120), nullable=True)

    vaccination_id = db.Column(db.Integer, db.ForeignKey("vaccination.id"), nullable=False)



class Vaccination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)

    #NYTT: Totalt antal doser
    total_doses = db.Column(db.Integer, nullable=False, default=1)

    # NYTT: Vaccination -> Person
    person_id = db.Column(db.Integer, db.ForeignKey("person.id"), nullable=False)

   # doses = db.relationship("Dose", backref="vaccination", cascade="all, delete-orphan")

    doses = db.relationship(
    "Dose",
    backref="vaccination",
    cascade="all, delete-orphan",
    order_by=(
        case((Dose.date_taken == None, 1), else_=0),  # None sist
        Dose.date_taken.asc(),
        Dose.dose_number.asc(),
        Dose.id.asc()
    )
)
