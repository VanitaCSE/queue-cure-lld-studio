from app.models.problem import PracticeProblem


DEMO_LEARNER_ID = "demo-learner"


def _clinic_criteria() -> dict[str, object]:
	return {
		"requirements": [
			{"terms": ["patient", "patientprofile", "patient profile"], "points": 2, "title": "Patient concept is not explained"},
			{"terms": ["doctor", "physician", "clinician"], "points": 2, "title": "Doctor concept is not explained"},
			{"terms": ["queue token", "queuetoken", "token", "ticket", "queue entry"], "points": 2, "title": "Missing queue-token model", "where": "Classes and responsibilities", "why": "Without an object representing a queue token, it is difficult to track queue number, priority, assignment, and lifecycle state consistently.", "how_to_improve": "Consider adding a QueueToken or equivalent object with a token number, priority, current status, timestamps, and an optional assigned doctor.", "recommendation": "Add a QueueToken model with explicit lifecycle states."},
			{"terms": ["priority", "emergency", "urgent", "high priority"], "points": 3, "title": "Priority-handling rule is not explained", "where": "Relationships and main workflow or Assumptions and trade-offs", "why": "The scenario requires priority patients to be handled differently from normal patients. Without an explicit rule, next-patient selection is ambiguous.", "how_to_improve": "Describe a priority rule and consider a QueueStrategy or PriorityQueueStrategy that serves priority patients first and FIFO within the same priority group.", "recommendation": "Explain priority selection and FIFO ordering through a QueueStrategy."},
			{"terms": ["waiting", "called", "in_consultation", "in consultation", "completed", "cancelled", "canceled", "no_show", "no show", "status", "state"], "points": 4, "title": "Queue-token lifecycle is unclear", "where": "Classes and responsibilities", "why": "The system must distinguish waiting, called, in-consultation, completed, cancelled, and no-show cases. Without explicit state handling, workflow transitions can become inconsistent.", "how_to_improve": "Add token states or a state-transition method to QueueToken, and explain which service is allowed to change the status.", "recommendation": "Add explicit queue-token lifecycle states."},
			{"terms": ["notification", "notify", "sms", "email", "alert"], "points": 3, "title": "Patient-notification behavior is missing", "where": "Relationships and main workflow", "why": "Patients need to know when their turn approaches or when their token status changes.", "how_to_improve": "Introduce a NotificationService or NotificationChannel abstraction and describe when notifications are sent.", "recommendation": "Describe when patient notifications are triggered."},
			{"terms": ["cancel", "cancellation", "no show", "no-show", "noshow"], "points": 2, "title": "Cancellation and no-show handling is missing", "where": "Assumptions and trade-offs", "why": "A waiting queue becomes inaccurate if cancelled or absent patients remain eligible for selection.", "how_to_improve": "Describe cancel and no-show transitions and how the queue skips or removes inactive tokens.", "recommendation": "Describe cancellation and no-show handling."},
		],
		"responsibilities": {"concepts": ["patient", "doctor", "token", "queue service", "queueservice", "queue manager", "queuemanager"], "manager_terms": ["queue service", "queueservice", "queue manager", "queuemanager"]},
		"relationships": {"checks": [["patient", "token"], ["queue service", "creates"], ["select", "next token", "next patient", "queue strategy"], ["doctorassignment", "doctor assignment", "assign", "available doctor"], ["notification", "notify", "status change"]]},
	}


def _parking_criteria() -> dict[str, object]:
	return {
		"requirements": [
			{"terms": ["vehicle", "car", "motorcycle", "truck"], "points": 3, "title": "Vehicle model is not explained", "where": "Classes and responsibilities", "why": "The parking workflow needs a clear representation of vehicle identity and type so compatibility and entry rules can be applied consistently.", "how_to_improve": "Consider adding a Vehicle object with a type and the information needed for parking allocation.", "recommendation": "Add a Vehicle model with explicit vehicle types."},
			{"terms": ["parking spot", "parkingspot", "spot type", "spot"], "points": 3, "title": "Parking-spot model is not explained", "where": "Classes and responsibilities", "why": "Without a parking-spot object, the design cannot clearly represent availability, type, occupancy, or vehicle compatibility.", "how_to_improve": "Consider adding ParkingSpot with a spot type, availability state, and compatibility rule.", "recommendation": "Add a ParkingSpot model and compatibility rule."},
			{"terms": ["parking lot", "parkinglot", "parking service", "parkingservice"], "points": 3, "title": "Parking-lot coordination is not explained"},
			{"terms": ["ticket", "parking ticket"], "points": 3, "title": "Parking-ticket workflow is missing", "where": "Relationships and main workflow", "why": "A ticket should connect vehicle entry information to spot release and fee calculation at exit.", "how_to_improve": "Describe a ParkingTicket containing the vehicle, assigned spot, entry time, and active status.", "recommendation": "Describe the ParkingTicket lifecycle."},
			{"terms": ["fee", "pricing", "duration", "rate"], "points": 3, "title": "Parking-fee calculation is not explained", "where": "Relationships and main workflow", "why": "The system needs a clear responsibility for calculating fees from parking duration and applicable rules.", "how_to_improve": "Consider a PricingStrategy or FeeCalculator that receives entry and exit information.", "recommendation": "Explain fee calculation through a pricing strategy."},
			{"terms": ["available", "allocation", "assign", "release", "exit"], "points": 3, "title": "Parking allocation workflow is not explained"},
			{"terms": ["strategy", "policy", "compatible", "compatibility"], "points": 2, "title": "Parking policies are not extensible"},
		],
		"responsibilities": {"concepts": ["vehicle", "spot", "ticket", "parking lot", "parking service", "parkingservice"], "manager_terms": ["parking service", "parkingservice", "parking manager", "parkingmanager"]},
		"relationships": {"checks": [["vehicle", "spot"], ["parking service", "assign", "creates", "allocat"], ["ticket"], ["release", "exit"], ["fee", "pricing", "duration", "rate"]]},
	}


def _network_intrusion_criteria() -> dict[str, object]:
	return {
		"requirements": [
			{"terms": ["security event", "securityevent", "network event", "networkevent", "event"], "points": 3, "title": "Security-event model is not explained", "where": "Classes and responsibilities", "why": "The system needs a clear representation of incoming security events before they can be classified or turned into alerts.", "how_to_improve": "Consider a SecurityEvent or NetworkEvent object containing source, destination, event type, and timestamp.", "recommendation": "Add a SecurityEvent model with the event data needed for detection."},
			{"terms": ["alert"], "points": 3, "title": "Alert model is not explained", "where": "Classes and responsibilities", "why": "Important security events need a durable alert object so analysts can track ownership, severity, and lifecycle.", "how_to_improve": "Describe an Alert object with severity, status, event context, and assignment information.", "recommendation": "Add an Alert model with severity and lifecycle state."},
			{"terms": ["severity", "low", "medium", "high", "critical"], "points": 3, "title": "Alert-severity policy is not explained", "where": "Classes and responsibilities or Interfaces and extensibility choices", "why": "Analysts need a consistent way to distinguish the urgency of different alerts.", "how_to_improve": "Describe severity values and consider a SeverityPolicy that can evolve independently from alert creation.", "recommendation": "Explain severity assignment through a policy or strategy."},
			{"terms": ["lifecycle", "status", "new", "open", "acknowledged", "resolved", "closed"], "points": 3, "title": "Alert lifecycle is not explained", "where": "Classes and responsibilities", "why": "Alerts need explicit state transitions so acknowledgement and resolution remain consistent.", "how_to_improve": "Define alert statuses and explain which service or operation performs each transition.", "recommendation": "Describe the alert lifecycle and state transitions."},
			{"terms": ["analyst", "security analyst", "assignment", "assign"], "points": 2, "title": "Analyst assignment is not explained", "where": "Relationships and main workflow", "why": "The workflow needs a clear way to connect an alert with the analyst responsible for reviewing it.", "how_to_improve": "Describe how AlertManager assigns an alert to an available SecurityAnalyst and tracks ownership.", "recommendation": "Explain alert assignment to a security analyst."},
			{"terms": ["dedup", "duplicate", "same event", "fingerprint"], "points": 2, "title": "Alert deduplication is not explained", "where": "Assumptions and trade-offs", "why": "Repeated security events can create noisy duplicate alerts unless the design defines when they represent the same incident.", "how_to_improve": "Describe a deduplication key or policy based on event identity, source, type, and time window.", "recommendation": "Describe how duplicate events or alerts are handled."},
			{"terms": ["invalid", "incomplete", "validation", "missing field"], "points": 2, "title": "Invalid-event handling is not explained", "where": "Assumptions and trade-offs", "why": "Incomplete security events should not create misleading alerts or break the alert workflow.", "how_to_improve": "Explain whether invalid events are rejected, quarantined, or recorded for later inspection.", "recommendation": "Describe safe handling for invalid or incomplete events."},
		],
		"responsibilities": {"concepts": ["security event", "securityevent", "network event", "networkevent", "event", "alert", "alert manager", "alertmanager", "alert service", "alertservice", "analyst", "security analyst"], "manager_terms": ["alert manager", "alertmanager", "alert service", "alertservice"]},
		"relationships": {"checks": [["event", "alert"], ["detection", "rule", "policy", "classif"], ["assign", "analyst"], ["acknowledge", "ack", "resolve", "closed"], ["notification", "notify"]]},
	}


def get_initial_problem() -> PracticeProblem:
	return PracticeProblem(
		id=None,
		slug="clinic-queue-management",
		title="Design a Clinic Queue Management System",
		difficulty="Intermediate",
		summary=(
			"Design an extensible clinic workflow for patient registration, queue "
			"tokens, priority handling, doctor availability, consultation status, "
			"and patient notifications."
		),
		description=(
			"A multi-doctor clinic needs software to manage patient registration, "
			"waiting queues, priority cases, doctor availability, consultations, "
			"cancellations, no-shows, and patient notifications. Design the core "
			"object-oriented domain model and explain your choices. This is a "
			"design exercise: do not implement a real clinic application."
		),
		requirements=[
			"Register a patient and create one active queue token per patient.",
			"Support normal and priority patients.",
			"Select the next suitable patient for an available doctor.",
			"Track token states: WAITING, CALLED, IN_CONSULTATION, COMPLETED, CANCELLED, and NO_SHOW.",
			"Notify patients when their turn is approaching or when their status changes.",
			"Allow cancellation and no-show handling.",
			"Keep the design extensible for future notification channels and queue-selection rules.",
		],
		constraints=[
			"A patient must not have more than one active token.",
			"A doctor can have only one active consultation at a time.",
			"Priority patients are served before normal patients.",
			"FIFO applies within the same priority category.",
			"The learner should explicitly explain assumptions and trade-offs.",
			"The learner should focus on classes, responsibilities, interfaces, relationships, and behavior—not deployment architecture.",
		],
		rubric={
			"Requirements coverage": 20,
			"Responsibility design": 25,
			"Extensibility and abstractions": 20,
			"Relationships and workflow": 20,
			"Edge cases and trade-offs": 15,
		},
		criteria=_clinic_criteria(),
	)


def get_parking_lot_problem() -> PracticeProblem:
	return PracticeProblem(
		id=None,
		slug="parking-lot-management",
		title="Design a Parking Lot Management System",
		difficulty="Intermediate",
		summary=(
			"Design an extensible parking workflow for vehicle entry, suitable spot "
			"allocation, ticketing, vehicle exit, and parking fees."
		),
		description=(
			"Design a parking lot system that manages vehicle entry, parking spot "
			"allocation, vehicle exit, and parking fees. This is a design exercise: "
			"do not implement a real parking application."
		),
		requirements=[
			"Support different vehicle types such as car, motorcycle, and truck.",
			"Support different parking spot types appropriate for different vehicles.",
			"Assign an available suitable spot when a vehicle enters.",
			"Generate a parking ticket containing the vehicle and entry information.",
			"Release the parking spot when the vehicle exits.",
			"Calculate the parking fee based on the parking duration and applicable rules.",
			"Handle the case when no suitable parking spot is available.",
			"Allow additional vehicle types, spot types, or pricing strategies to be added later.",
		],
		constraints=[
			"A vehicle should occupy at most one active parking spot.",
			"A parking spot can hold only one vehicle at a time.",
			"A vehicle can exit only with a valid active parking ticket.",
			"Spot compatibility should be kept separate from fee calculation.",
			"The learner should explicitly explain assumptions and trade-offs.",
			"The learner should focus on classes, responsibilities, interfaces, relationships, and behavior—not deployment architecture.",
		],
		rubric={
			"Requirements coverage": 20,
			"Responsibility design": 25,
			"Extensibility and abstractions": 20,
			"Relationships and workflow": 20,
			"Edge cases and trade-offs": 15,
		},
		criteria=_parking_criteria(),
	)


def get_initial_problems() -> list[PracticeProblem]:
	return [get_initial_problem(), get_parking_lot_problem(), get_network_intrusion_alert_manager_problem()]


def get_network_intrusion_alert_manager_problem() -> PracticeProblem:
	return PracticeProblem(
		id=None,
		slug="network-intrusion-alert-manager",
		title="Network Intrusion Alert Manager",
		difficulty="Intermediate",
		summary=(
			"Design a system that receives network security events, converts important "
			"events into alerts, assigns severity, manages alert lifecycle, and notifies "
			"security analysts."
		),
		description=(
			"Design a small object-oriented system for managing cybersecurity alerts. "
			"It receives network security events, identifies important activity, tracks "
			"alert status and severity, supports analyst review, and communicates changes. "
			"Keep the design focused on domain objects, responsibilities, relationships, "
			"policies, and behavior rather than machine-learning or deployment architecture."
		),
		requirements=[
			"Accept security events containing information such as source, destination, event type, and timestamp.",
			"Detect or classify important events that should become alerts.",
			"Assign an alert severity such as LOW, MEDIUM, HIGH, or CRITICAL.",
			"Create and track an alert with a clear lifecycle.",
			"Allow analysts to acknowledge and resolve alerts.",
			"Support assigning an alert to a security analyst.",
			"Avoid creating duplicate alerts for the same event when appropriate.",
			"Allow new detection rules, severity policies, or notification channels to be added later.",
			"Handle invalid or incomplete security events safely.",
		],
		constraints=[
			"An invalid or incomplete event should not create an unsafe alert.",
			"Repeated events may need deduplication within a defined policy or time window.",
			"Alert lifecycle changes should be explicit and auditable.",
			"The learner should explain assumptions and trade-offs for detection and notification.",
			"The learner should focus on classes, responsibilities, interfaces, relationships, and behavior—not deployment architecture.",
		],
		rubric={
			"Requirements coverage": 20,
			"Responsibility design": 25,
			"Extensibility and abstractions": 20,
			"Relationships and workflow": 20,
			"Edge cases and trade-offs": 15,
		},
		criteria=_network_intrusion_criteria(),
	)