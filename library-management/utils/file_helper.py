"""
utils/file_helper.py
─────────────────────
Handles file uploads — validates extension,
generates unique filename, saves to disk.
"""

import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def save_cover_image(file) -> str | None:
    """
    Save an uploaded book cover image.
    Returns the filename (not full path) or None if invalid.
    """
    if not file or file.filename == "":
        return None
    if not allowed_file(file.filename):
        return None

    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    safe_name = secure_filename(unique_name)

    upload_folder = os.path.join(
        current_app.root_path,
        current_app.config["UPLOAD_FOLDER"]
    )
    os.makedirs(upload_folder, exist_ok=True)

    file.save(os.path.join(upload_folder, safe_name))
    return safe_name


def delete_file(filename: str) -> None:
    """Delete a file from the uploads folder."""
    if not filename or filename == "default_cover.png":
        return
    upload_folder = os.path.join(
        current_app.root_path,
        current_app.config["UPLOAD_FOLDER"]
    )
    path = os.path.join(upload_folder, filename)
    if os.path.exists(path):
        os.remove(path)