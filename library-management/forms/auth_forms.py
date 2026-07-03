from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models import User


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[
        DataRequired(message="Email is required"),
        Email(message="Enter a valid email")
    ])
    password = PasswordField("Password", validators=[
        DataRequired(message="Password is required")
    ])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class RegisterForm(FlaskForm):
    full_name = StringField("Full Name", validators=[
        DataRequired(message="Full name is required"),
        Length(min=2, max=120, message="Name must be 2-120 characters")
    ])
    email = StringField("Email", validators=[
        DataRequired(message="Email is required"),
        Email(message="Enter a valid email")
    ])
    role = SelectField("Register As", choices=[
        ("student",   "Student"),
        ("librarian", "Librarian"),
    ])
    student_id = StringField("Student ID", validators=[
        Length(max=50)
    ])
    department = StringField("Department", validators=[
        Length(max=100)
    ])
    password = PasswordField("Password", validators=[
        DataRequired(message="Password is required"),
        Length(min=6, message="Password must be at least 6 characters")
    ])
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo("password", message="Passwords must match")
    ])
    submit = SubmitField("Create Account")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError("This email is already registered.")

    def validate_student_id(self, field):
        if field.data and User.query.filter_by(student_id=field.data).first():
            raise ValidationError("This Student ID is already registered.")


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[
        DataRequired(message="Email is required"),
        Email(message="Enter a valid email")
    ])
    submit = SubmitField("Send Reset Link")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[
        DataRequired(message="Password is required"),
        Length(min=6, message="Password must be at least 6 characters")
    ])
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo("password", message="Passwords must match")
    ])
    submit = SubmitField("Reset Password")