from flask import Flask, render_template, redirect, url_for, flash, abort, request
from flask_bootstrap import Bootstrap
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import *
from flask_ckeditor import CKEditor
from functools import wraps
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
bootstrap = Bootstrap(app)

ckeditor = CKEditor(app)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# SET LOGIN MANAGER
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# CONFIGURE TABLES
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    questions = relationship("Question", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")


class Question(db.Model):
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="questions")
    title = db.Column(db.String(140), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)

    # ***************Parent Relationship*************#
    comments = relationship("Comment", back_populates="parent_question")


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")
    text = db.Column(db.Text, nullable=False)

    # ***************Child Relationship*************#
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"))
    parent_question = relationship("Question", back_populates="comments")


db.create_all()


@app.route('/')
def home():
    if current_user.is_authenticated:
        return render_template("full_homepage.html")
    return render_template("blank_start.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterUserForm()
    if register_form.validate_on_submit():
        database_match = User.query.filter_by(email=register_form.email.data).first()
        if database_match:
            error = 'E-mail already exists'
            flash('This e-mail adress is already registered. Try another one.')
            return redirect(url_for('register', error=error))
        new_user = User(
            email=register_form.email.data,
            password=generate_password_hash(register_form.password.data, method='pbkdf2:sha256', salt_length=8),
            name=register_form.name.data
        )
        db.session.add(new_user)
        db.session.commit()
        load_user(new_user.id)
        login_user(new_user)
        return redirect(url_for('home'))
    return render_template("register.html", form=register_form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data
        database_match = User.query.filter_by(email=email).first()
        if not database_match:
            error = 'Invalid credentials'
            flash('E-mail adress not registered, please try again or sign up.')
            return redirect(url_for('login', error=error))
        elif not check_password_hash(database_match.password, password):
            error = 'Password incorrect'
            flash('Password incorrect, please try again.')
            return redirect(url_for('login', error=error))
        else:
            load_user(database_match.id)
            login_user(database_match)
            return redirect(url_for('home'))
    return render_template("login.html", form=login_form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/new-question', methods=['GET', 'POST'])
def new_question():
    question_form = NewQuestion()
    if question_form.validate_on_submit():
        title = question_form.title.data
        text = question_form.body.data
        question = Question(author=current_user,
                            title=title,
                            date=date.today().strftime("%B %d, %Y"),
                            body=text)
        db.session.add(question)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('new-question.html', form=question_form)


@app.route('/my-profile')
def my_profile():
    pass


if __name__ == "__main__":
    app.run(debug=True)

