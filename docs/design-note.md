# Design Note: Queue-Cure LLD Studio

## 1. System Overview

Queue-Cure LLD Studio is a Flask learning platform for practicing Low-Level Design. It is not a clinic queue-management application. The current learner flow is:

```text
Problem
  |
  v
Attempt
  |
  v
Draft Submission
  |
  v
Submit
  |
  v
EvaluationService
  |
  v
Evaluator
  |
  v
EvaluationResult
  |
  v
Feedback
  |
  v
History
```

A learner selects one of the seeded problems, starts an attempt, saves structured design text, submits the saved design, and receives feedback. Draft saving is allowed to be incomplete. Final submission validation requires non-blank classes and relationships text, a minimum combined amount of core design detail, and field length limits.

The failure and retry path is:

```text
Evaluation failure
  |
  v
EVALUATION_FAILED
  |
  v
Feedback + Retry
  |
  v
Same Attempt
  |
  v
Evaluation
  |
  v
FEEDBACK_READY
```

Evaluation currently runs synchronously in the submit request. The status still records the logical evaluation phases.

## 2. Domain Model

### `PracticeProblem`

Defined in `app.models.problem`. It contains the problem identity and learner brief: `id`, `slug`, `title`, `difficulty`, `summary`, `description`, requirements, constraints, rubric maximums, and problem-specific evaluation `criteria`.

### `Attempt`

Defined in `app.models.attempt`. It identifies one learner's work for one problem and stores `learner_id`, `problem_id`, status, creation/update timestamps, and optional submission time.

### `Submission`

Defined in `app.models.submission`. It stores the learner's structured design text:

- `classes_text`
- `relationships_text`
- `extensibility_text`
- `tradeoffs_text`
- `diagram_text`

### `EvaluationResult`

Defined in `app.models.evaluation`. It stores the evaluator name, overall score, category scores, strengths, findings, recommendations, safe error message, and creation timestamp.

### `FeedbackFinding`

Defined in `app.models.feedback`. It stores a finding's category, severity, title, location, explanation, and improvement guidance. Findings are stored inside evaluation JSON fields; there is no separate findings table.

### `Evaluator`

Defined as a protocol in `app.evaluators.evaluator`. Its contract is `evaluate(problem, submission) -> EvaluationResult`.

### `RuleBasedEvaluator`

Defined in `app.evaluators.rule_based_evaluator`. It is the current evaluator implementation. It normalizes text and applies deterministic phrase matching against criteria from the selected `PracticeProblem`.

There is no separate `EvaluationRule` class. Evaluation rules are represented as dictionaries in each problem's `criteria` configuration.

## 3. Data Persistence

SQLite is initialized from `app/schema.sql`. The current tables are:

### `problems`

- `id` primary key
- `slug` unique and not null
- `title`
- `difficulty`
- `summary`
- `description`
- `requirements_json`
- `constraints_json`
- `rubric_json`

`rubric_json` stores the rubric scores and the problem's criteria configuration. JSON conversion occurs at the model/repository boundary.

### `attempts`

- `id` primary key
- `learner_id`
- `problem_id`
- `status`
- `created_at`
- `updated_at`
- `submitted_at`
- foreign key to `problems(id)`

Indexes support learner history ordering and problem lookup.

### `submissions`

- `id` primary key
- `attempt_id` unique and not null
- the five structured text fields, each not null with an empty-string default
- foreign key to `attempts(id)` with `ON DELETE CASCADE`

The unique `attempt_id` means one current submission is associated with an attempt.

### `evaluations`

- `id` primary key
- `attempt_id` unique and not null
- `evaluator_name`
- `overall_score`
- JSON fields for category scores, strengths, findings, and recommendations
- `error_message`
- `created_at`
- foreign key to `attempts(id)` with `ON DELETE CASCADE`

The unique `attempt_id` and repository upsert ensure one current evaluation result per attempt.

SQLite foreign keys are enabled when a connection is opened.

## 4. Evaluation Design

The evaluator protocol receives both the selected problem and the learner submission. `RuleBasedEvaluator` then:

1. Normalizes the five submission text fields case-insensitively.
2. Reads criteria from `PracticeProblem.criteria`.
3. Calculates category scores from detected evidence.
4. Caps scores at the problem rubric maximums.
5. Produces strengths supported by detected evidence.
6. Produces de-duplicated findings with severity and learner-facing explanations.
7. Produces at most three recommendations.

The five current categories and maximum scores are:

| Category | Maximum |
| --- | ---: |
| Requirements coverage | 20 |
| Responsibility design | 25 |
| Extensibility and abstractions | 20 |
| Relationships and workflow | 20 |
| Edge cases and trade-offs | 15 |

The overall score is the sum of category scores, bounded to the 0-100 range. Matching is deterministic keyword/phrase matching, not semantic natural-language understanding.

## 5. Problem Extensibility

The initializer seeds exactly three problems:

1. Clinic Queue Management (`clinic-queue-management`)
2. Parking Lot Management (`parking-lot-management`)
3. Network Intrusion Alert Manager (`network-intrusion-alert-manager`)

Each problem has the same `PracticeProblem` shape, the same five rubric categories, and its own criteria dictionary. The generic evaluator consumes those criteria rather than selecting a scoring implementation by slug. There are no normal evaluator branches of the form `if problem X, use X scoring`.

The same routes and services handle all three problems:

```text
GET /problems
GET /problems/<slug>
POST /problems/<slug>/attempts
POST /attempts/<id>/save
POST /attempts/<id>/submit
GET /attempts/<id>/feedback
GET /history
```

The current submission format is the five text fields plus optional Mermaid text. A future format, such as a richer diagram payload or another structured editor, could be adapted at the service boundary into the existing `Submission` contract; that adapter is not implemented today.

## 6. Attempt Lifecycle

The actual `AttemptStatus` values are:

- `DRAFT`
- `SUBMITTED`
- `EVALUATING`
- `FEEDBACK_READY`
- `EVALUATION_FAILED`

Implemented transitions:

```text
DRAFT -> SUBMITTED -> EVALUATING -> FEEDBACK_READY
                         |
                         v
                 EVALUATION_FAILED
                         |
                         v
                     EVALUATING
```

Draft attempts can be saved. Final submission validation occurs before the first status transition. Only draft attempts can be submitted. Only failed evaluations can be retried. Submitted, evaluating, feedback-ready, and failed attempts are not editable as drafts.

## 7. Failure and Retry Behavior

The submission is persisted during draft saving before evaluation. On submit, `EvaluationService` loads that persisted submission and validates it before changing status.

If the evaluator raises an unexpected exception:

- The exception is logged with attempt and learner context.
- A safe failure `EvaluationResult` is upserted when persistence is available.
- The attempt is moved to `EVALUATION_FAILED` where possible.
- The original submission remains unchanged.
- The learner sees `We could not evaluate this attempt. Please try again.` rather than a traceback.
- Feedback exposes a retry action.

Retry uses the same attempt and submission. A successful retry stores the successful result, changes status to `FEEDBACK_READY`, and replaces the failure row through the evaluation upsert. The unique evaluation-to-attempt relationship prevents duplicate current results.

## 8. UI Flow

The current Jinja/Bootstrap UI includes:

- **Problem catalog:** lists the three seeded problems with problem-specific tags.
- **Problem details:** shows summary, description, requirements, constraints, rubric, and a start-attempt form.
- **Attempt editor:** supports five structured text fields, draft saving, final submission, and read-only display after submission.
- **Feedback page:** shows status, overall score, qualitative score label, category scores, strengths, findings, recommendations, and the original submission. Failed evaluations show the safe error message and retry action.
- **History page:** lists attempt ID, problem title, status, timestamps, score when available, and the appropriate continue/view-feedback action.

## 9. Testing Strategy

The test suite uses Flask's test client and temporary SQLite databases configured through `tests/conftest.py`. The latest full run reports **53 passing tests**.

Coverage includes:

- Database tables, foreign keys, and idempotent initialization
- Problem catalog and detail routes
- Attempt creation, draft saving, and history
- Submission validation and draft preservation
- Clinic, Parking Lot, and Network Intrusion workflows
- Generic evaluator criteria and hypothetical third-problem support
- Scores, findings, strengths, recommendations, and determinism
- Evaluation failure, safe feedback, retry, submission preservation, and duplicate prevention
- Edge routes, learner scoping, repeated lifecycle actions, failed history states, and escaped learner content

## 10. Architecture Decisions

- **Flask:** provides a small server-rendered web application and application factory.
- **Service layer:** keeps attempt and evaluation workflow decisions out of route functions.
- **Repository layer:** keeps SQLite SQL and row conversion out of services and templates.
- **SQLite:** is sufficient for a focused prototype with one fixed `demo-learner` context.
- **Deterministic evaluator:** provides stable, explainable feedback without external cost or latency.

The application intentionally avoids distributed infrastructure, background workers, queues, Redis, and microservices because the assignment is a small learning prototype and does not require those operational boundaries.

## 11. Known Limitations

- The learner context is fixed to `demo-learner`; there is no authentication or account system.
- Matching is deterministic keyword/phrase matching and does not understand semantics deeply.
- Evaluation is synchronous and has no distributed worker queue.
- There is no LLM evaluator.
- Submitted attempts are immutable; creating an improved attempt is not implemented as a separate workflow.
- The README is a concise setup and submission overview; this note provides the detailed implementation design.
