# Research Note: Explainable LLD Evaluation

## 1. Problem

A learner submitting a Low-Level Design should receive feedback that helps them improve their reasoning, not only a correct/incorrect result. Low-Level Design is rarely a problem with one universally correct class diagram. Two designs can choose different names, ownership boundaries, or abstractions and still be reasonable if they cover the requirements and explain their trade-offs.

Comparing every submission with one golden implementation creates several problems. It rewards imitation instead of design reasoning, treats alternative but valid structures as errors, and hides why a choice may be useful or risky. Generic feedback has the opposite problem: it may sound encouraging but does not tell the learner which requirement was missed, where the responsibility is unclear, or what to improve first. Useful feedback should connect an observation to the submitted text and to a concrete design concern.

## 2. Existing Approaches and Tools

Several existing resources show useful parts of the practice problem, but they are not a complete match for this small platform:

| Approach/tool | What it provides | Strength | Gap for this assignment |
| --- | --- | --- | --- |
| Educative, *Grokking the Low Level Design Interview Using OOD Principles* | Structured OOD instruction, real-world design problems, UML diagrams, implementation exercises, and mock interviews | Gives learners repetition and a repeatable way to break down open-ended problems | It is a course and interview-preparation product; this assignment needs a small local workflow that stores a learner's own attempt and produces immediate criteria-based feedback |
| Refactoring.Guru design-pattern catalog | Explanations and examples of common design patterns, organized by intent and category | Useful reference vocabulary for responsibilities, abstractions, and extensibility | A pattern reference does not evaluate whether a learner applied a suitable responsibility split to a particular problem or track improvement across attempts |
| Mermaid class-diagram documentation and editor | Text-based class-diagram syntax, relationships, members, interfaces, and a live editor | Makes a learner's optional structural design easy to write and inspect as text | Diagram rendering alone does not judge requirements coverage, trade-offs, lifecycle choices, or the quality of the surrounding explanation |

Sources:

- Educative, *Grokking the Low Level Design Interview Using OOD Principles*: https://www.educative.io/courses/grokking-the-low-level-design-interview-using-ood-principles
- Refactoring.Guru, Design Patterns: https://refactoring.guru/design-patterns
- Mermaid, Class diagrams syntax: https://mermaid.js.org/syntax/classDiagram.html

These sources were used as reference points for existing practice resources, design vocabulary, and diagram tooling. They are not presented as user research or as a benchmark for this prototype.

## 3. Key Gaps

The reviewed approaches emphasize learning content, pattern reference, diagrams, or interview practice. They do not directly provide the combination required here: a learner chooses a problem, stores a structured design attempt, receives feedback tied to explicit design dimensions, and reviews the same learner's history. A single expected answer would also be too rigid for LLD, while unstructured qualitative feedback can be difficult to reproduce and test consistently.

The resulting gap is not the absence of design education. It is the lack of a small, inspectable loop that turns a learner's own explanation into actionable, repeatable feedback without pretending that one class diagram is universally correct.

## 4. Product Direction

The MVP direction is:

```text
Choose Problem
   |
   v
Practice
   |
   v
Submit
   |
   v
Explainable Evaluation
   |
   v
Feedback
   |
   v
History
   |
   v
Try Again
```

The implemented product focuses on deterministic feedback for requirements coverage, responsibility allocation, extensibility, relationships/workflow, and edge cases/trade-offs. It stores attempts and shows feedback so the learner can practice repeatedly. The evaluator protocol and problem-owned criteria leave a small extension point for another evaluator later. LLM-assisted qualitative review, richer semantic analysis, accounts, analytics, and advanced diagram analysis remain future ideas rather than current functionality.

## 5. Current Evaluation Approach

Queue-Cure LLD Studio currently uses a deterministic rule-based evaluator. A learner submits structured text for:

- Classes and responsibilities
- Relationships and main workflow
- Interfaces and extensibility choices
- Assumptions and trade-offs
- Optional Mermaid diagram text

The evaluator normalizes the text and performs case-insensitive keyword and phrase matching. It evaluates five categories:

| Category | Maximum |
| --- | ---: |
| Requirements coverage | 20 |
| Responsibility design | 25 |
| Extensibility and abstractions | 20 |
| Relationships and workflow | 20 |
| Edge cases and trade-offs | 15 |

The result contains an overall score, category scores, strengths, explainable findings, and up to three recommendations. Findings include a category, severity, title, location in the submission, explanation of why the issue matters, and a possible improvement.

This approach is appropriate for the current prototype because it is local, inexpensive, repeatable, and easy to inspect. A learner can see why a finding was produced. The evaluator is deliberately a baseline rather than a claim of complete natural-language understanding.

## 6. Why Not Only Use an LLM?

An LLM could produce richer qualitative commentary, but using one as the only evaluator would introduce trade-offs:

- **Determinism:** identical submissions may receive different wording or scores.
- **Repeatability:** test expectations and learner comparisons become harder to stabilize.
- **Explainability:** the system may not be able to show a precise rule behind a judgment.
- **Cost and latency:** each evaluation may require a remote request and incur usage cost.
- **Consistency:** scores can drift with prompt, model, or configuration changes.
- **Hallucination risk:** feedback may assert a requirement or class that is not in the problem.
- **Subjectivity:** broad design questions can be judged inconsistently without a constrained rubric.

The current architecture leaves room for a future evaluator implementation. Another class can implement the existing `Evaluator` protocol and return the same `EvaluationResult`. Routes, `EvaluationService`, SQLite persistence, and feedback templates do not need to know whether the result came from deterministic rules or a future qualitative evaluator. No LLM evaluator is currently implemented.

## 7. Evaluation Architecture

The evaluator boundary is:

```text
PracticeProblem + Submission
             |
             v
          Evaluator
             |
             v
      EvaluationResult
```

`Evaluator` is a Python protocol with `evaluate(problem, submission)`. `RuleBasedEvaluator` implements it. The evaluator receives the selected problem rather than assuming the Clinic Queue problem.

Each `PracticeProblem` contains category maximums in `rubric` and problem-owned matching criteria in `criteria`. The criteria describe terms, points, responsibility concepts, and relationship checks. The three seeded problems use this same structure:

- Clinic Queue Management
- Parking Lot Management
- Network Intrusion Alert Manager

The evaluator consumes those criteria through shared scoring and finding logic. There are no normal-execution branches that select a separate evaluator by problem slug. This keeps problem-specific concepts near the problem definition while keeping category scoring centralized.

## 8. Reliability

Evaluation is synchronous in the current prototype, but submission durability is handled before evaluation starts. Draft text is stored in the `submissions` table. On submit, `EvaluationService` loads that stored submission, validates it, moves the attempt through `SUBMITTED` and `EVALUATING`, and then invokes the evaluator.

If evaluation raises an exception, the service stores a failure `EvaluationResult` with a learner-safe message and changes the attempt to `EVALUATION_FAILED`. The original submission is not deleted or replaced. The learner can open feedback, see the failure, and retry the same attempt. A successful retry stores the current result and changes the attempt to `FEEDBACK_READY`.

The database has a unique constraint on `evaluations.attempt_id`, and repository persistence uses an upsert. Therefore an attempt has one current evaluation result rather than accumulating confusing duplicate results during retries. Submitted attempts are immutable through both route and service checks.

## 9. Product and Engineering Trade-offs

This project intentionally remains a focused Flask monolith. The assignment needs a learner workflow, a small SQLite persistence layer, and explainable evaluation. Adding microservices, Redis, background queues, Kubernetes, or a distributed workflow engine would increase operational and conceptual cost without improving the core learning outcome in this prototype.

A service layer keeps workflow decisions out of routes. A repository layer keeps SQL out of services and templates. SQLite is sufficient for a fixed demo learner and a small local prototype. These choices preserve clarity and make the current behavior straightforward to test.

## 10. Future Work

The following are future possibilities, not current features:

- Qualitative LLM-assisted feedback behind the same evaluator protocol
- Richer semantic analysis of relationships and responsibilities
- Evaluator versioning and comparison of evaluation runs
- Analytics for learner progress and repeated weaknesses
- Multiple learner accounts and authentication
- Richer diagram parsing and consistency checks
- More advanced relationship or similarity analysis

The current implementation intentionally stops at deterministic, explainable matching.
