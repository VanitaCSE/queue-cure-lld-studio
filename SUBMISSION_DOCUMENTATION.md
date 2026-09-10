# LLD Practice Platform — Documentation

## 1. Project Overview

Queue-Cure LLD Studio is a focused Low-Level Design practice and evaluation platform built with Flask, SQLite, Jinja templates, Bootstrap 5, and pytest. It is a learning platform, not a real clinic queue-management application.

## 2. Features

### Learner Workflow

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

### Current Problems

The database is seeded with exactly three problems:

1. **Clinic Queue Management**
2. **Parking Lot Management**
3. **Network Intrusion Alert Manager**

Each problem uses the same `PracticeProblem` model, rubric categories, attempt workflow, evaluation service, feedback page, and history page. Problem-specific matching criteria are stored with the problem definition.

### Evaluation Features

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

### Testing and Validation

The test suite uses temporary SQLite databases through pytest fixtures. The latest validation run completed:

```text
53 passed
```

The suite covers database initialization, problem routes, all three problem workflows, draft and final validation, evaluator criteria and determinism, feedback rendering, failure/retry behavior, duplicate prevention, edge cases, learner scoping, and safe rendering of learner content.

## 3. Learner Journey

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

## 4. Evaluation Approach

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

## 5. Architecture

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

## 6. Reliability and Failure Handling

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

## 7. How to Run the Project

### Setup on Windows PowerShell

```powershell
cd "C:\Users\Lenovo\OneDrive\Desktop\queue-cure-lld-studio"
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

### Initialize and Run

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

## 8. Key Design Decisions

- The database is seeded with exactly three problems.
- Each problem uses the same `PracticeProblem` model, rubric categories, attempt workflow, evaluation service, feedback page, and history page.
- Problem-specific matching criteria are stored with the problem definition.
- The application uses the `Evaluator` protocol and the production `RuleBasedEvaluator`.
- Routes handle HTTP concerns and templates. Services own attempt and evaluation workflow decisions. Repositories contain SQLite SQL and row conversion.
- Domain models are dataclasses independent of Flask requests and templates.
- The evaluator consumes `PracticeProblem` plus `Submission` and returns `EvaluationResult`.
- The evaluation table has a unique `attempt_id`, and repository upsert behavior prevents duplicate current evaluation rows.

## 9. Limitations

Current limitations:

- The learner context is fixed to `demo-learner`; there is no authentication or account system.
- Matching is deterministic keyword/phrase matching, not semantic natural-language understanding.
- Evaluation runs synchronously in the submit request.
- There is no LLM evaluator, distributed worker, or external evaluation service.
- Submitted attempts are immutable; an improved-attempt creation workflow is not implemented.

Possible future work includes richer semantic analysis, evaluator versioning, multiple learners, richer diagram checks, analytics, and optional qualitative evaluation behind the existing evaluator protocol. These are not implemented in the current repository.

See [docs/research-note.md](docs/research-note.md) for evaluation reasoning and [docs/design-note.md](docs/design-note.md) for the detailed implementation design.

## 10. AI Usage Report

# AI Usage

AI was used as a development assistant during the implementation and review of Queue-Cure LLD Studio. It supported repository exploration, focused implementation suggestions, test generation, debugging, edge-case review, and documentation consistency checks. The developer reviewed the suggestions, accepted or rejected them, ran the tests, and made the product and architecture decisions.

## Four AI-Assisted Decisions

| Decision | What AI suggested or assisted with | What the developer decided | Why |
| --- | --- | --- | --- |
| Evaluator architecture | Introduce an `Evaluator` protocol and a deterministic `RuleBasedEvaluator` returning structured `EvaluationResult` data | Accepted the abstraction and deterministic evaluator; rejected adding an LLM or a larger evaluation framework | The protocol leaves a replacement point, while deterministic results are explainable, repeatable, and appropriate for a focused two-day MVP |
| Problem extensibility | Audit found that problem-specific evaluator behavior could become slug-based branches | Accepted moving criteria into `PracticeProblem.criteria`; rejected a complicated generic rules engine | Criteria stay with the problem, support the three scenarios and hypothetical problems, and keep shared evaluator logic small |
| Evaluation failure and retry | Audit the lifecycle so evaluator failure cannot lose learner work | Accepted persisting submissions before evaluation, storing failure state, retrying the same attempt, and using evaluation upsert/uniqueness | Learner work must survive failure, and reliability can be achieved without queues or distributed infrastructure |
| Validation and edge-case hardening | Inspect whether existing validation and lifecycle behavior already met the requirements, then add targeted tests and investigate failures | Kept existing service validation, added focused regression tests, and made only the minimal history-template fix for `Evaluation_Failed` and `None` score display | Avoids unnecessary production changes while improving coverage and fixing a genuine learner-facing presentation defect |

These examples reflect actual implementation and review work in the repository. AI did not independently design or implement the entire project.

## Human Judgment and Responsibility

The developer was responsible for:

- Defining the learner workflow and the three LLD problem scenarios
- Choosing a focused Flask plus SQLite monolith instead of unnecessary infrastructure
- Selecting the five evaluation categories and their weights
- Reviewing evaluator behavior and deciding that feedback should not depend on one golden class diagram
- Deciding that criteria should be configuration-driven through `PracticeProblem.criteria`
- Reviewing failure/retry behavior, submission immutability, and duplicate evaluation handling
- Investigating test failures before deciding whether code or test expectations were wrong
- Manually verifying successful and failed workflows across the three problems
- Verifying that README, research note, design note, and this file match the actual code

## AI-Assisted Development Workflow

```text
Audit
  |
  v
Understand existing implementation
  |
  v
AI suggests focused change
  |
  v
Developer reviews and accepts/rejects approach
  |
  v
Implement
  |
  v
Run tests
  |
  v
Inspect failures
  |
  v
Fix or adjust
  |
  v
Run full regression
  |
  v
Manually verify
```

AI output was reviewed and validated rather than accepted blindly. Changes were kept close to the relevant service, repository, route, template, or test surface.

## Validation

The project was validated with:

- Pytest using temporary SQLite databases
- Python `compileall`
- Database initialization checks
- Problem route and workflow checks
- Submission validation tests
- Evaluation failure and retry tests
- Duplicate evaluation and immutability tests
- Manual smoke tests across all three seeded problems
- Full regression testing

The latest full test run reports **53 passing tests**.

Final validation commands:

```powershell
flask --app run.py init-db
python -m compileall -q run.py app tests
pytest -q
```

## AI Limitations

AI suggestions can contain incorrect assumptions, miss repository-specific behavior, or propose unnecessary changes. Repository inspection, executable tests, compile checks, rendered-route checks, and human review were used to verify behavior.

AI assistance does not replace decisions about product scope, domain modeling, evaluation fairness, reliability, security boundaries, or whether a suggested change is appropriate for the assignment.

## 11. Future Work

Possible future work includes richer semantic analysis, evaluator versioning, multiple learners, richer diagram checks, analytics, and optional qualitative evaluation behind the existing evaluator protocol. These are not implemented in the current repository.
