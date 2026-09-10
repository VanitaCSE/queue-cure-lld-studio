import os
from pathlib import Path

from flask import Flask

from app.config import Config
from app.db import close_db, init_db_command
from app.routes.attempts import bp as attempts_bp
from app.routes.history import bp as history_bp
from app.routes.main import bp as main_bp
from app.routes.problems import bp as problems_bp


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object(Config)
    app.config.from_mapping(DATABASE=os.path.join(app.instance_path, "lld_studio.db"))

    if test_config is not None:
        app.config.from_mapping(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

    app.register_blueprint(main_bp)
    app.register_blueprint(problems_bp)
    app.register_blueprint(attempts_bp)
    app.register_blueprint(history_bp)

    @app.errorhandler(404)
    def not_found(error):
        return render_error("Page not found", "The page you requested does not exist."), 404

    return app


def render_error(title, message):
    from flask import render_template

    return render_template("error.html", title=title, message=message)