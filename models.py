from flask import Flask
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
db = SQLAlchemy()



class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(8), unique=True)
    google_email = db.Column(db.String(256), unique=True)
    google_name = db.Column(db.String(256))
    user_name = db.Column(db.String(256), unique=True)
    email = db.Column(db.String(256), unique=True)
    password = db.Column(db.String(256))

    def __init__(self, unique_id, google_email, google_name, user_name, email, password):
        self.unique_id = unique_id
        self.google_email = google_email
        self.google_name = google_name
        self.user_name = user_name
        self.email = email
        if password is not None:
            self.password = generate_password_hash(password)
        else:
            self.password = password

    def check_password(self, password):
        return check_password_hash(self.password, password)


class OAuth(OAuthConsumerMixin, db.Model):
    provider_user_id = db.Column(db.String(256), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(Users.id), nullable=False)
    user = db.relationship(Users)


login_manager = LoginManager()
login_manager.login_view = 'signup'


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))
