# LLD Practice Platform

Queue-Cure LLD Studio is a focused Low-Level Design practice and evaluation platform built with Flask, SQLite, Jinja templates, Bootstrap 5, and pytest. It is a learning platform, not a real clinic queue-management application.

## Learner Workflow

```text
Choose LLD Problem
	|
	v
Start Attempt
	|
	v
Create/Save Design
	|
	v
Submit
	|
	v
Deterministic Evaluation
	|
	v
Feedback
	|
	v
History
	|
	v
Retry / Practice Again
```

Learners describe classes and responsibilities, relationships and workflow, extensibility choices, assumptions and trade-offs, and an optional Mermaid diagram. Drafts may be incomplete; final submission validation requires enough core design detail for evaluation.

## Current Problems

The database is seeded with exactly three problems:

1. **Clinic Queue Management**
2. **Parking Lot Management**
3. **Network Intrusion Alert Manager**

Each problem uses the same `PracticeProblem` model, rubric categories, attempt workflow, evaluation service, feedback page, and history page. Problem-specific matching criteria are stored with the problem definition.

## Evaluation

Evaluation is deterministic and local. The application uses the `Evaluator` protocol and the production `RuleBasedEvaluator`; it does not currently use an LLM or external evaluation API.

The evaluator reads the selected problem's criteria, normalizes submitted text, performs keyword/phrase matching, and creates explainable results. Feedback includes:

- Overall score from 0 to 100
- Category scores
- Strengths
- Findings with severity, location, rationale, and improvement guidance
- Up to three recommendations

The current rubric categories are:

| Category | Maximum score |
| --- | ---: |
| Requirements coverage | 20 |
| Responsibility design | 25 |
| Extensibility and abstractions | 20 |
| Relationships and workflow | 20 |
| Edge cases and trade-offs | 15 |

## Architecture

```text
Flask Routes
     |
     v
Services
     |
     v
Repositories
     |
     v
SQLite
```

Evaluation uses a separate abstraction:

```text
Evaluator Protocol
	 |
	 v
RuleBasedEvaluator
```

Routes handle HTTP concerns and templates. Services own attempt and evaluation workflow decisions. Repositories contain SQLite SQL and row conversion. Domain models are dataclasses independent of Flask requests and templates. The evaluator consumes `PracticeProblem` plus `Submission` and returns `EvaluationResult`.

## Attempt Lifecycle

The actual attempt statuses are:

- `DRAFT`
- `SUBMITTED`
- `EVALUATING`
- `FEEDBACK_READY`
- `EVALUATION_FAILED`

Normal flow:

```text
DRAFT -> SUBMITTED -> EVALUATING -> FEEDBACK_READY
```

Failure and retry flow:

```text
EVALUATING -> EVALUATION_FAILED -> EVALUATING -> FEEDBACK_READY
```

A submission is persisted before evaluation begins. If evaluation fails, the original submission remains available, a safe failure result is stored, and the same attempt can be retried. The evaluation table has a unique `attempt_id`, and repository upsert behavior prevents duplicate current evaluation rows. Submitted work cannot be edited through the route or service layer.

## Testing

The test suite uses temporary SQLite databases through pytest fixtures. The latest validation run completed:

```text
53 passed
```

The suite covers database initialization, problem routes, all three problem workflows, draft and final validation, evaluator criteria and determinism, feedback rendering, failure/retry behavior, duplicate prevention, edge cases, learner scoping, and safe rendering of learner content.

Run the tests with:

```powershell
pytest -q
```

## Project Structure

```text
queue-cure-lld-studio/
├── run.py
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── README.md
├── AI_USAGE.md
├── docs/
│   ├── research-note.md
│   └── design-note.md
├── instance/
│   └── lld_studio.db          # created by init-db, ignored by Git
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── db.py
│   ├── schema.sql
│   ├── models/
│   ├── repositories/
│   ├── services/
│   ├── evaluators/
│   ├── routes/
│   ├── templates/
│   └── static/
└── tests/
    ├── conftest.py
    └── test_*.py
```

## Setup on Windows PowerShell

```powershell
cd "C:\Users\Lenovo\OneDrive\Desktop\queue-cure-lld-studio"
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

## Initialize and Run

Initialize the SQLite schema and seed the three problems:

```powershell
flask --app run.py init-db
```

The database is created at `instance\lld_studio.db`.

Run the application:

```powershell
python run.py
```

Open http://127.0.0.1:5000.

Run compilation and tests:

```powershell
python -m compileall -q run.py app tests
pytest -q
```

## Known Limitations and Future Work

Current limitations:

- The learner context is fixed to `demo-learner`; there is no authentication or account system.
- Matching is deterministic keyword/phrase matching, not semantic natural-language understanding.
- Evaluation runs synchronously in the submit request.
- There is no LLM evaluator, distributed worker, or external evaluation service.
- Submitted attempts are immutable; an improved-attempt creation workflow is not implemented.

Possible future work includes richer semantic analysis, evaluator versioning, multiple learners, richer diagram checks, analytics, and optional qualitative evaluation behind the existing evaluator protocol. These are not implemented in the current repository.

See [docs/research-note.md](docs/research-note.md) for evaluation reasoning and [docs/design-note.md](docs/design-note.md) for the detailed implementation design.