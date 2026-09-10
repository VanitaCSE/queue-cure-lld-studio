import sqlite3

import click
from flask import current_app, g

from app.repositories.sqlite_problem_repository import SQLiteProblemRepository
from app.services.problem_catalog import get_initial_problems


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(error=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()
    with current_app.open_resource("schema.sql") as schema_file:
        db.executescript(schema_file.read().decode("utf-8"))
    problem_repository = SQLiteProblemRepository(db)
    for problem in get_initial_problems():
        problem_repository.seed_problem(problem)
    db.commit()


@click.command("init-db")
def init_db_command():
    """Create the application database tables."""
    init_db()
    click.echo("Initialized the database.")