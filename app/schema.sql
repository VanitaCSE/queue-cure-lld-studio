CREATE TABLE IF NOT EXISTS problems (
    id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    summary TEXT NOT NULL,
    description TEXT NOT NULL,
    requirements_json TEXT NOT NULL,
    constraints_json TEXT NOT NULL,
    rubric_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY,
    learner_id TEXT NOT NULL,
    problem_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    submitted_at TEXT,
    FOREIGN KEY (problem_id) REFERENCES problems (id)
);

CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY,
    attempt_id INTEGER UNIQUE NOT NULL,
    classes_text TEXT NOT NULL DEFAULT '',
    relationships_text TEXT NOT NULL DEFAULT '',
    extensibility_text TEXT NOT NULL DEFAULT '',
    tradeoffs_text TEXT NOT NULL DEFAULT '',
    diagram_text TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (attempt_id) REFERENCES attempts (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY,
    attempt_id INTEGER UNIQUE NOT NULL,
    evaluator_name TEXT NOT NULL,
    overall_score INTEGER,
    category_scores_json TEXT,
    strengths_json TEXT,
    findings_json TEXT,
    recommendations_json TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (attempt_id) REFERENCES attempts (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_attempts_learner_created
    ON attempts (learner_id, created_at);

CREATE INDEX IF NOT EXISTS idx_attempts_problem
    ON attempts (problem_id);

CREATE INDEX IF NOT EXISTS idx_evaluations_attempt
    ON evaluations (attempt_id);