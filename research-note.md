# Research Note — LLD Practice Platform

## 1. Learner Problem

Low-level design practice is easy to start because the prompt is usually simple: pick a domain, identify the main entities, and sketch a model. The difficulty is in judging whether the design is correct, complete, and maintainable. Learners can often describe a few classes, but they struggle to decide whether responsibilities are assigned well, whether abstractions are strong enough, whether relationships reflect the real workflow, and whether edge cases are handled consistently. In LLD, the common weak spots are not just missing classes; they are unclear ownership, mixed responsibilities, shallow abstractions, missing workflows, weak extensibility, and poor trade-off reasoning.

This matters because learners are often evaluating their own designs against a vague standard. They may not know which gaps are structural versus implementation-level, or how to reason about an extensible design rather than a one-off solution. The problem is not simply generating a diagram. It is judging whether the design makes sense under change, failure, and ambiguous requirements. That is why useful, explainable feedback matters: learners need to understand not only whether they scored well, but also what was missing, why it matters, and what to improve next.

## 2. Existing Approaches / Tools Researched

- Educative / Grokking the Low-Level Design Interview using OOD Principles: This provides structured learning on LLD interview preparation, object-oriented design principles, and common design problem patterns. It helps learners study the concepts behind good system design. The remaining gap for this assignment is that it is a learning resource rather than an interactive practice loop with submission, evaluation, and feedback.
- Refactoring.Guru Design Patterns: This provides explanations, examples, and reference material for design patterns and common design vocabulary. It helps learners reason about abstraction and extensibility. The remaining gap is that it does not provide a problem-based practice workflow, a submission model, or a grading system for learner submissions.
- Mermaid class diagrams: This provides a way to express class relationships visually using class diagram syntax. It helps learners communicate structure and relationships. The remaining gap is that a diagram is still a manual artifact; it does not evaluate whether the design covers responsibilities, trade-offs, edge cases, or the required workflow in a repeatable and explainable way.

## 3. Key Gaps

The research suggests a clear gap: learning resources help learners study LLD, and diagram/design tools help them express a design, but neither automatically turns learning into a focused practice loop. The learner still needs a place to choose a problem, write a design, submit it, receive explainable evaluation, review actionable feedback, and revisit prior attempts over time. The current project addresses that gap by combining problem definitions, structured submission fields, deterministic matching against problem criteria, category-based scoring, and a simple history view.

## 4. Product Direction

The focused MVP is a practice loop built around a single, simple flow: Choose Problem → Start Attempt → Design → Save Draft → Submit → Evaluate → Review Feedback → View History → Practice Again.

This repository currently implements three LLD problems: Clinic Queue Management, Parking Lot Management, and Network Intrusion Alert Manager. Each attempt stores structured submission fields for classes, relationships, extensibility, trade-offs, and an optional Mermaid diagram. Final submission validation requires enough core design detail before the evaluation step begins. The evaluation itself is deterministic and local: the production evaluator is a rule-based implementation rather than an LLM or an external service. The current rubric uses five categories: Requirements coverage, Responsibility design, Extensibility and abstractions, Relationships and workflow, and Edge cases and trade-offs.

The feedback output includes strengths, findings, and actionable improvements, and the application records evaluation results and attempt history. The current implementation also includes failure/retry handling: if evaluation fails unexpectedly, the system stores a safe failure result and keeps the original submission available; a failed attempt can be retried. This is a focused MVP for LLD practice and does not claim broader LMS, authentication, or asynchronous evaluation features.

Future ideas are not implemented in the current codebase. Examples include richer semantic evaluation, multi-learner accounts, broader submission formats, and asynchronous or external evaluation infrastructure. The current repository is intentionally limited to a simple, deterministic evaluation practice loop.

## 5. Product Principles

- Focus on LLD/domain design rather than a large learning-management system.
- Feedback should be explainable and actionable, not opaque or purely numeric.
- Evaluation should be deterministic and repeatable for the MVP, without depending on external services.
- Keep the architecture simple while allowing future evaluators or submission formats to plug in behind the current interfaces.
- Validate important failure and edge cases, especially around draft submissions, short designs, re-evaluation, and safe error handling.

## References

- https://www.educative.io/courses/grokking-the-low-level-design-interview-using-ood-principles
- https://refactoring.guru/design-patterns
- https://mermaid.js.org/syntax/classDiagram.html
