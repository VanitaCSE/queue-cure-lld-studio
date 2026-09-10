from app.db import get_db, init_db


def test_init_db_seeds_both_problems(app):
    with app.app_context():
        problem_count = get_db().execute("SELECT COUNT(*) FROM problems").fetchone()[0]
        slugs = {
            row["slug"]
            for row in get_db().execute("SELECT slug FROM problems").fetchall()
        }

    assert problem_count == 3
    assert slugs == {
        "clinic-queue-management",
        "parking-lot-management",
        "network-intrusion-alert-manager",
    }


def test_init_db_does_not_duplicate_problem(app):
    runner = app.test_cli_runner()
    first_result = runner.invoke(args=["init-db"])
    second_result = runner.invoke(args=["init-db"])

    with app.app_context():
        problem_count = get_db().execute("SELECT COUNT(*) FROM problems").fetchone()[0]

    assert first_result.exit_code == 0, first_result.output
    assert second_result.exit_code == 0, second_result.output
    assert problem_count == 3


def test_init_db_creates_all_tables(app):
    with app.app_context():
        init_db()
        table_names = {
            row["name"]
            for row in get_db().execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert {"problems", "attempts", "submissions", "evaluations"} <= table_names


def test_foreign_keys_are_enabled(app):
    with app.app_context():
        foreign_keys_enabled = get_db().execute("PRAGMA foreign_keys").fetchone()[0]

    assert foreign_keys_enabled == 1


def test_init_db_command_can_run_repeatedly(app):
    runner = app.test_cli_runner()

    first_result = runner.invoke(args=["init-db"])
    second_result = runner.invoke(args=["init-db"])

    assert first_result.exit_code == 0, first_result.output
    assert second_result.exit_code == 0, second_result.output
