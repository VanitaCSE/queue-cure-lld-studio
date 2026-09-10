from app.evaluators.rule_based_evaluator import RuleBasedEvaluator
from app.models.problem import PracticeProblem
from app.models.submission import Submission
from app.services.problem_catalog import get_initial_problem


def submission(**overrides):
    values = {
        "classes_text": "",
        "relationships_text": "",
        "extensibility_text": "",
        "tradeoffs_text": "",
        "diagram_text": "",
    }
    values.update(overrides)
    return Submission(id=None, attempt_id=1, **values)


def titles(result):
    return {finding.title for finding in result.findings}


def test_weak_submission_reports_missing_core_concepts():
    result = RuleBasedEvaluator().evaluate(
        get_initial_problem(),
        submission(classes_text="Patient and Doctor are classes."),
    )

    assert result.overall_score < 40
    assert "Missing queue-token model" in titles(result)
    assert "Priority-handling rule is not explained" in titles(result)
    assert all(
        finding.where and finding.why and finding.how_to_improve
        for finding in result.findings
    )


def test_structured_submission_scores_higher_and_has_strengths():
    result = RuleBasedEvaluator().evaluate(
        get_initial_problem(),
        submission(
            classes_text=(
                "Patient owns identity. QueueToken stores priority, WAITING, "
                "CALLED, and COMPLETED states. Doctor tracks availability. "
                "QueueService coordinates responsibilities."
            ),
            relationships_text=(
                "QueueService creates a QueueToken for a Patient, uses QueueStrategy "
                "for priority and FIFO selection, assigns the token to an available "
                "Doctor, and triggers NotificationChannel on state changes."
            ),
            extensibility_text=(
                "QueueStrategy supports priority and FIFO policies. "
                "NotificationChannel has SMS and email implementations."
            ),
            tradeoffs_text=(
                "Assume one active token per patient. Cancellation and no-show mark "
                "tokens inactive. Doctor unavailability returns a token to WAITING."
            ),
        ),
    )

    assert result.overall_score > 40
    assert len(result.strengths) >= 3
    assert "Missing queue-token model" not in titles(result)
    assert "Priority-handling rule is not explained" not in titles(result)


def test_god_class_finding_is_not_duplicated():
    result = RuleBasedEvaluator().evaluate(
        get_initial_problem(),
        submission(
            classes_text=(
                "QueueManager creates patient tokens, selects the next patient, "
                "assigns doctors, sends notifications, changes token status, and "
                "saves records to the database."
            )
        ),
    )

    assert sum(
        finding.title == "Queue coordination may have too many responsibilities"
        for finding in result.findings
    ) == 1


def test_missing_tradeoffs_is_reported():
    result = RuleBasedEvaluator().evaluate(
        get_initial_problem(),
        submission(
            classes_text="Patient, QueueToken, Doctor, and QueueService classes.",
            relationships_text="QueueService creates QueueToken and assigns Doctor.",
        ),
    )

    assert "Assumptions and trade-offs are not explained" in titles(result)


def test_evaluation_is_deterministic_except_for_timestamp():
    evaluator = RuleBasedEvaluator()
    problem = get_initial_problem()
    design = submission(
        classes_text="Patient and QueueToken with status and priority.",
        relationships_text="QueueService creates QueueToken and assigns Doctor.",
        extensibility_text="QueueStrategy and NotificationChannel interface.",
        tradeoffs_text="FIFO within priority and cancellation is a state change.",
    )

    first = evaluator.evaluate(problem, design)
    second = evaluator.evaluate(problem, design)

    assert first.overall_score == second.overall_score
    assert first.category_scores == second.category_scores
    assert first.strengths == second.strengths
    assert [finding.title for finding in first.findings] == [
        finding.title for finding in second.findings
    ]
    assert first.recommendations == second.recommendations


def test_scores_respect_problem_rubric_limits():
    result = RuleBasedEvaluator().evaluate(
        get_initial_problem(),
        submission(
            classes_text="Patient Doctor QueueToken QueueService QueueStrategy NotificationChannel.",
            relationships_text="QueueService creates, selects, assigns, and notifies.",
            extensibility_text="interface repository strategy SMS email.",
            tradeoffs_text="Priority FIFO cancellation no-show unavailable active token assumptions.",
        ),
    )

    assert result.overall_score <= 100
    for category, score in result.category_scores.items():
        assert score <= get_initial_problem().rubric[category]


def test_hypothetical_problem_uses_problem_owned_criteria():
    problem = PracticeProblem(
        id=None,
        slug="bank-account-demo",
        title="Design an Account Transaction Ledger",
        difficulty="Intermediate",
        summary="Practice account transaction modeling.",
        description="A hypothetical third problem used only in this test.",
        requirements=["Model accounts and transactions."],
        constraints=["Keep transaction history auditable."],
        rubric=get_initial_problem().rubric,
        criteria={
            "requirements": [
                {
                    "terms": ["account"],
                    "points": 5,
                    "title": "Account concept is not explained",
                    "where": "Classes and responsibilities",
                    "why": "An account is needed to own the balance and transaction context.",
                    "how_to_improve": "Consider adding an Account object with clear ownership of balance state.",
                    "recommendation": "Add an Account model.",
                },
                {
                    "terms": ["transaction"],
                    "points": 5,
                    "title": "Transaction concept is not explained",
                    "where": "Classes and responsibilities",
                    "why": "Transactions represent auditable changes to an account.",
                    "how_to_improve": "Describe a Transaction object and its lifecycle.",
                    "recommendation": "Describe transaction state and history.",
                },
            ],
            "responsibilities": {
                "concepts": ["account", "transaction", "history"],
                "manager_terms": ["ledger service"],
            },
            "relationships": {"checks": [["account", "transaction"], ["history"]]},
        },
    )
    design = submission(
        classes_text="Account owns balance. Transaction records each change. TransactionHistory stores an audit trail.",
        relationships_text="LedgerService applies a Transaction to an Account and appends it to TransactionHistory.",
        extensibility_text="TransactionPolicy is an interface.",
        tradeoffs_text="The history is append-only so account changes remain auditable.",
    )

    result = RuleBasedEvaluator().evaluate(problem, design)

    assert result.overall_score > 0
    assert result.category_scores["Requirements coverage"] == 10
    assert "Account concept is not explained" not in titles(result)
    assert "Transaction concept is not explained" not in titles(result)