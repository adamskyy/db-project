from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Regexp, Length, Email, EqualTo, ValidationError
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Regexp(r'^[a-zA-Z0-9_]*$', message='Username can only contain letters, numbers, and underscores'), Length(min=8, max=20, message='Username must be between 8 and 20 characters long')])
    password = PasswordField('Password', validators=[DataRequired(), Regexp(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,20}$', message='Password must be 8-20 characters long and contain letters and numbers')])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Regexp(r'^[a-zA-Z0-9_]*$', message='Username can only contain letters, numbers, and underscores'), Length(min=8, max=20, message='Username must be between 8 and 20 characters long')])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Regexp(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,20}$', message='Password must be 8-20 characters long and contain letters and numbers')])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired(), Regexp(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,20}$', message='Password must be 8-20 characters long and contain letters and numbers')])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')