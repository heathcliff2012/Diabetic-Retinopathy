from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from retinopathy.modules import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=20)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')
     
    def validate_username(self, username):
            user = User.query.filter_by(username = username.data).first()
            if user:
                 raise ValidationError('username already exists')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=20)])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class UpdateAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('update')

class PatientForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    age = StringField('Age', validators=[DataRequired()])
    sex = StringField('Sex', validators=[DataRequired()])
    patient_id = StringField('Patient ID', validators=[DataRequired()])
    right_eye_diagnosis = StringField('Right Eye Diagnosis', validators=[DataRequired()])
    left_eye_diagnosis = StringField('Left Eye Diagnosis', validators=[DataRequired()])
    right_eye_image = StringField('Right Eye Image', validators=[DataRequired()])
    left_eye_image = StringField('Left Eye Image', validators=[DataRequired()])
    submit = SubmitField('Add Patient')