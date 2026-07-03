"""
forms/borrow_forms.py
──────────────────────
Forms for issuing and returning books.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional


class IssueBookForm(FlaskForm):
    student_email = StringField("Student Email", validators=[
        DataRequired(message="Student email is required")
    ])
    book_id = IntegerField("Book ID", validators=[
        DataRequired(message="Book ID is required"),
        NumberRange(min=1, message="Enter a valid book ID")
    ])
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Issue Book")


class ReturnBookForm(FlaskForm):
    borrow_id = IntegerField("Borrow Record ID", validators=[
        DataRequired(message="Borrow record ID is required"),
        NumberRange(min=1)
    ])
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Accept Return")