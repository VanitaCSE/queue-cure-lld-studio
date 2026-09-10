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
