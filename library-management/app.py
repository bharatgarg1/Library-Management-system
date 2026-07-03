import os
from flask_wtf.csrf import CSRFProtect
from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from config import config_map
from models import db, bcrypt, User, Role, Category

migrate = Migrate()
login_manager = LoginManager()
mail = Mail()


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_map[config_name])
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    CSRFProtect(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    _configure_login_manager(app)
    _register_blueprints(app)

    with app.app_context():
        db.create_all()
        _seed_initial_data()

    return app


def _configure_login_manager(app):
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))


def _register_blueprints(app):
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.librarian import librarian_bp
    from routes.student import student_bp
    from routes.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp,      url_prefix="/auth")
    app.register_blueprint(admin_bp,     url_prefix="/admin")
    app.register_blueprint(librarian_bp, url_prefix="/librarian")
    app.register_blueprint(student_bp,   url_prefix="/student")


def _seed_initial_data():
    roles_data = [
        ("super_admin", "Full system access"),
        ("librarian",   "Manage books and borrowing"),
        ("student",     "Search, borrow, and return books"),
    ]
    for name, desc in roles_data:
        if not Role.query.filter_by(name=name).first():
            db.session.add(Role(name=name, description=desc))
    db.session.flush()

    categories = [
        ("Computer Science", "Programming, algorithms, networks", "bi-laptop"),
        ("Mathematics",      "Calculus, algebra, statistics",    "bi-calculator"),
        ("Physics",          "Classical and modern physics",     "bi-lightning"),
        ("Literature",       "Fiction, poetry, drama",           "bi-book-half"),
        ("History",          "World and regional history",       "bi-hourglass"),
        ("Science",          "Biology, chemistry, earth science","bi-flask"),
        ("Self Help",        "Personal development and mindset", "bi-star"),
        ("Engineering",      "Civil, mechanical, electrical",    "bi-gear"),
    ]
    for name, desc, icon in categories:
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name, description=desc, icon=icon))

    admin_role = Role.query.filter_by(name="super_admin").first()
    if admin_role and not User.query.filter_by(email="admin@library.com").first():
        admin = User(
            full_name="Super Admin",
            email="admin@library.com",
            role_id=admin_role.id,
            is_active=True,
            email_verified=True,
        )
        admin.set_password("Admin@1234")
        db.session.add(admin)

    db.session.commit()


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)