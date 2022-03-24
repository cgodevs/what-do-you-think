from flask import Flask, render_template, redirect, url_for, flash, abort, request
from flask_bootstrap import Bootstrap
from datetime import date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import *
from math import ceil
from flask_ckeditor import CKEditor
from functools import wraps
import os
from sqlalchemy import or_
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
bootstrap = Bootstrap(app)
ckeditor = CKEditor(app)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///database.db")  # 'sqlite:///database.db'
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
    name = db.Column(db.String(100), unique=True)
    questions = relationship("Question", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")
    received_dms = relationship("DirectMessage", back_populates="recipient")


class Question(db.Model):
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="questions")
    title = db.Column(db.String(140), nullable=False)
    date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(140), nullable=False)
    body = db.Column(db.Text, nullable=False)
    upvotes = db.Column(db.Integer, default=0)
    # ***************Parent Relationship*************#
    comments = relationship("Comment", back_populates="parent_question")


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")
    date = db.Column(db.Date, nullable=False)
    text = db.Column(db.Text, nullable=False)

    # ***************Child Relationship*************#
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"))
    parent_question = relationship("Question", back_populates="comments")


class DirectMessage(db.Model):
    __tablename__ = "dms"
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    recipient = relationship("User", back_populates="received_dms")
    author = db.Column(db.String(250), nullable=False)
    date = db.Column(db.Date, nullable=False)
    text = db.Column(db.Text, nullable=False)


db.create_all()


@app.route('/')
def home():
    if current_user.is_authenticated:
        return mainpage(1)
    return render_template("blank_start.html")


@app.route('/mainpage/<int:pagination>')
def mainpage(pagination):
    if current_user.is_authenticated:
        if db.session.query(Question).first():
            all_latest_questions = db.session.query(Question).order_by(Question.id.desc()).filter(date.today() - Question.date <= 10)
            number_of_pages = int(ceil(all_latest_questions.count() / 6))
            page_questions = all_latest_questions[(pagination - 1) * 6: (pagination - 1) * 6 + 6]
            most_upvoted_question = db.session.query(Question).order_by(Question.id.desc()).first()     # last record
            for question in all_latest_questions:
                if question.upvotes > most_upvoted_question.upvotes:
                    most_upvoted_question = question    # featured question is the most upvoted in the last 10 days or the last ever record
            return render_template("full_homepage.html",
                                   pagination=pagination,
                                   featured_question=most_upvoted_question,
                                   questions=page_questions,
                                   pages=number_of_pages)
    return render_template("blank_start.html")


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterUserForm()
    if register_form.validate_on_submit():
        database_email_match = User.query.filter_by(email=register_form.email.data).first()
        if database_email_match:
            error = 'E-mail already exists'
            flash('This e-mail adress is already registered. Try another one.')
            return redirect(url_for('register', error=error))
        database_username_match = User.query.filter_by(name=register_form.name.data).first()
        if database_username_match:
            error = 'Username already exists'
            flash('This username is already in use. Try another one.')
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
        category = question_form.category.data
        question = Question(author=current_user,
                            title=title,
                            date=date.today(),  # .strftime("%B %d, %Y")
                            category=category,
                            body=text)
        db.session.add(question)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('new-question.html', form=question_form)


@app.route('/my-profile/<menu_action>', methods=['GET', 'POST'])
def my_profile(menu_action):
    if menu_action == 'reset-pw':
        if request.method == 'POST':
            old_pw = request.form.get("old-pw")
            new_pw = request.form.get("new-pw")
            database_match_pw = User.query.filter_by(email=current_user.email).first().password
            if old_pw == "" or new_pw == "":
                pass
            elif not check_password_hash(database_match_pw, old_pw):
                flash('Password incorrect.')
            elif check_password_hash(database_match_pw, new_pw):
                flash('New password cannot be equal to the last one.')
            else:
                User.query.filter_by(email=current_user.email).first().password = generate_password_hash(new_pw, method='pbkdf2:sha256', salt_length=8)
                db.session.commit()
                flash('Password changed successfully!.')
        return render_template('reset-pw.html')
    elif menu_action == 'reset-address':
        if request.method == 'POST':
            new_address = request.form.get("new-address")
            User.query.filter_by(email=current_user.email).first().email = new_address
            db.session.commit()
            flash('Address  changed successfully')
        return render_template('reset-address.html')
    elif menu_action == 'sent-questions':
        user_questions = Question.query.filter_by(author=current_user)
        return render_template('sent-questions.html', questions=user_questions)
    elif menu_action == 'dms':
        return render_template('dms.html')


@app.route('/user/<username>')
def user_page(username):
    user_obj = User.query.filter_by(name=username).first()
    return render_template('user-profile.html', user=user_obj)


@app.route('/<username>/send-dm', methods=['GET', 'POST'])
def send_dm(username):
    user_obj = User.query.filter_by(name=username).first()
    dm_form = DMForm()
    if dm_form.validate_on_submit():
        text = dm_form.body.data
        new_dm = DirectMessage(recipient=user_obj,
                               recipient_id=user_obj.id,
                               author=current_user.name,
                               date=date.today(),   #.strftime("%B %d, %Y")
                               text=text)
        db.session.add(new_dm)
        db.session.commit()
        return render_template('user-profile.html', user=user_obj)
    return render_template('send-dm.html', user=user_obj, form=dm_form)


@app.route("/delete-dm/<int:dm_id>")
def delete_dm(dm_id):
    dm_to_delete = DirectMessage.query.get(dm_id)
    db.session.delete(dm_to_delete)
    db.session.commit()
    return redirect(url_for('my_profile', menu_action='dms'))


@app.route("/question/<int:q_id>", methods=['GET', 'POST'])
def show_question(q_id):
    comment_form = CommentForm()
    db_question = Question.query.get(q_id)
    if db_question:
        if comment_form.validate_on_submit():
            comment_text = comment_form.body.data
            new_comment = Comment(author_id=current_user.id,
                                  comment_author=current_user,
                                  date=date.today(),    # .strftime("%B %d, %Y")
                                  text=comment_text,
                                  question_id=q_id,
                                  parent_question=db_question)
            db.session.add(new_comment)
            db.session.commit()
        return render_template('question-page.html', question=db_question, comment_form=comment_form)
    else:
        return abort(404)


@app.route("/upvote/<int:q_id>")
def upvote_question(q_id):
    db_question = Question.query.get(q_id)
    db_question.upvotes += 1
    db.session.commit()     # a bug here is the user can upvote the post infinitely
    return redirect(url_for('show_question', q_id=q_id))


@app.route("/delete-question/<int:q_id>")
def delete_question(q_id):
    q_to_delete = Question.query.get(q_id)
    db.session.delete(q_to_delete)
    db.session.commit()
    return redirect(url_for('my_profile', menu_action='sent-questions'))


@app.route("/delete-comment/<int:q_id>/<int:comment_id>")
def delete_comment(q_id, comment_id):
    comment_to_delete = Comment.query.get(comment_id)
    db.session.delete(comment_to_delete)
    db.session.commit()
    return redirect(url_for('show_question', q_id=q_id))


@app.route("/search/<category>")
def search(category):
    chosen_category = category
    all_category_questions = db.session.query(Question) \
        .filter_by(category=chosen_category) \
        .order_by(Question.id.desc())
    return render_template('category-questions.html',
                           questions=all_category_questions,
                           category=category)


@app.route("/search/by-words", methods=['GET', 'POST'])
def search_tool():
    if request.method == 'POST':
        search_keys = request.form.get("search-keys")
        match_questions = db.session.query(Question) \
            .filter(or_(Question.body.contains(search_keys),Question.title.contains(search_keys))) \
            .order_by(Question.id.desc())
    return render_template('search-tool.html', questions=match_questions)


@app.route("/search/all-categories")
def all_categories():
    return render_template('all-categories.html', categories=CATEGORIES)


if __name__ == "__main__":
    app.run(debug=True)

