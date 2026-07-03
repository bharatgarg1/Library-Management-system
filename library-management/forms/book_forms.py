"""
forms/book_forms.py
────────────────────
WTForms for adding and editing books.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, TextAreaField, IntegerField,
    SelectField, SubmitField
)
from wtforms.validators import DataRequired, Length, Optional, NumberRange


class BookForm(FlaskForm):
    title = StringField("Book Title", validators=[
        DataRequired(message="Title is required"),
        Length(max=255)
    ])
    isbn = StringField("ISBN", validators=[Optional(), Length(max=20)])
    description = TextAreaField("Description", validators=[Optional()])
    author_name = StringField("Author Name", validators=[
        DataRequired(message="Author name is required"),
        Length(max=150)
    ])
    category_id = SelectField("Category", coerce=int, validators=[
        DataRequired(message="Please select a category")
    ])
    publisher = StringField("Publisher", validators=[Optional(), Length(max=150)])
    published_year = IntegerField("Published Year", validators=[
        Optional(),
        NumberRange(min=1000, max=2100, message="Enter a valid year")
    ])
    language = StringField("Language", validators=[Optional(), Length(max=50)])
    pages = IntegerField("Pages", validators=[
        Optional(),
        NumberRange(min=1, message="Pages must be positive")
    ])
    edition = StringField("Edition", validators=[Optional(), Length(max=50)])
    location = StringField("Shelf Location", validators=[Optional(), Length(max=100)])
    total_copies = IntegerField("Total Copies", validators=[
        DataRequired(message="Total copies required"),
        NumberRange(min=1, message="Must have at least 1 copy")
    ], default=1)
    cover_image = FileField("Cover Image", validators=[
        FileAllowed(["jpg", "jpeg", "png", "gif", "webp"],
                    "Images only (jpg, png, gif, webp)")
    ])
    submit = SubmitField("Save Book")