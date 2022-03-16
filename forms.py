from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, TextAreaField, SelectField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditorField


class RegisterUserForm(FlaskForm):
    name = StringField("Username", validators=[DataRequired()])
    email = StringField("E-mail", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("E-mail", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")


class NewQuestion(FlaskForm):
    title = StringField("Question Title", validators=[DataRequired()])
    category = SelectField("Pick a Category",
                           choices=[('Career', 'Career'), ('Relationship', 'Relationship'),
                                    ('Selfies', 'Selfies'), ('Fitness', 'Fitness'),
                                    ('Risks', 'Risks'), ('Games', 'Games'),
                                    ('Programming', 'Programming'), ('Writers', 'Writers'),
                                    ('Pictures', 'Pictures')])
    body = CKEditorField("Question Body", validators=[DataRequired()])
    submit = SubmitField("Ask")


class DMForm(FlaskForm):
    body = TextAreaField("Message", validators=[DataRequired()])
    submit = SubmitField("Send")


class CommentForm(FlaskForm):
    body = TextAreaField("Comment", validators=[DataRequired()])
    submit = SubmitField("Send Comment")
