"""
SAATVIKA — Orchestrator
========================
The single entry point for all user interactions. Routes messages to the
appropriate sub-agent based on context and conversation state.

Architecture:
  User → Orchestrator → {IntakeAgent, LegalAgent, FinancialAgent, EngagementAgent}
                      ← Assembled response back to user

State Machine:
  INTAKE → ACTIVE → FOLLOW_UP → COMPLETE

IQ Layers: All three — Foundry IQ, Fabric IQ, Work IQ — via sub-agents.
"""
from typing import Optional
from datetime import datetime

from .intake_agent import IntakeAgent
from .legal_agent import LegalAgent
from .financial_agent import FinancialAgent
from .engagement_agent import EngagementAgent


class Orchestrator:
    """
    Coordinates all sub-agents and maintains conversation state.
    The user only ever talks to the Orchestrator.
    """

    STATES = ["INTAKE", "ACTIVE", "FOLLOW_UP", "COMPLETE"]

    # Keywords that route to each agent
    LEGAL_KEYWORDS = [
        "death certificate", "register", "legal heir", "succession",
        "probate", "will", "property", "mutation", "court", "lawyer",
        "document", "certificate", "tehsildar", "magistrate",
    ]
    FINANCIAL_KEYWORDS = [
        "bank", "account", "insurance", "lic", "epf", "provident fund",
        "pension", "home loan", "mortgage", "gratuity", "claim", "money",
        "funds", "transfer", "nominee", "fd", "fixed deposit",
    ]
    ENGAGEMENT_KEYWORDS = [
        "remind", "reminder", "support", "help", "grief", "counselling",
        "mental health", "helpline", "overwhelmed", "sad", "resources",
        "ngo", "legal aid", "how am i doing", "progress",
    ]

    def __init__(self):
        self.state = "INTAKE"
        self.case_profile: Optional[dict] = None
        self.conversation_history: list[dict] = []
        self.session_start = datetime.now().isoformat()

        # Initialize all agents
        self.intake_agent = IntakeAgent()
        self.legal_agent = LegalAgent()
        self.financial_agent = FinancialAgent()
        self.engagement_agent = EngagementAgent()

    def process_message(self, user_message: str,
                        intake_data: Optional[dict] = None) -> dict:
        """
        Main entry point. Process any user message and return a response.

        Args:
            user_message: Free-text message from the family
            intake_data: Structured intake form data (if submitting intake)

        Returns:
            Orchestrated response dict
        """
        msg_lower = user_message.lower().strip()

        # Record message in history
        self.conversation_history.append({
            "role": "user",
            "message": user_message,
            "timestamp": datetime.now().isoformat(),
            "state": self.state,
        })

        # --- State: INTAKE ---
        if self.state == "INTAKE" or intake_data:
            if intake_data:
                response = self._handle_intake(intake_data)
            else:
                response = self._intake_welcome()

        # --- State: ACTIVE — route to appropriate agent ---
        elif self.state == "ACTIVE":
            response = self._route_to_agent(msg_lower, user_message)

        # --- State: FOLLOW_UP ---
        elif self.state == "FOLLOW_UP":
            response = self._handle_follow_up(msg_lower, user_message)

        # --- State: COMPLETE ---
        else:
            response = self._handle_complete()

        # Record response
        self.conversation_history.append({
            "role": "saatvika",
            "agent": response.get("agent", "Orchestrator"),
            "timestamp": datetime.now().isoformat(),
            "state": self.state,
        })

        return self._wrap_response(response)

    def _intake_welcome(self) -> dict:
        """Return the welcome message prompting intake form completion."""
        return {
            "agent": "Orchestrator",
            "state": "INTAKE",
            "message": (
                "Namaste. I am Saatvika — here to help your family navigate "
                "the administrative and legal steps after this loss.\n\n"
                "I will guide you through every step with grounded, cited guidance "
                "from official government sources. I will never give you advice "
                "without citing where it comes from.\n\n"
                "To get started, please fill in the details below so I can understand "
                "your situation and create a personalised task plan for you."
            ),
            "action_required": "complete_intake_form",
            "intake_form_fields": [
                {"field": "deceased_name", "label": "Name of deceased", "type": "text", "required": True},
                {"field": "date_of_death", "label": "Date of death", "type": "date", "required": True},
                {"field": "state", "label": "State (where deceased lived)", "type": "text", "required": True},
                {"field": "city", "label": "City / District", "type": "text", "required": True},
                {"field": "employment_type", "label": "Employment type",
                 "type": "select", "options": ["government", "government_retired", "private_sector", "self_employed", "not_employed"], "required": True},
                {"field": "has_property", "label": "Did deceased own property (house/land/flat)?", "type": "boolean", "required": True},
                {"field": "has_bank_accounts", "label": "Did deceased have bank accounts?", "type": "boolean", "required": True},
                {"field": "bank_account_count", "label": "How many bank accounts?", "type": "number", "required": False},
                {"field": "has_nominee_bank", "label": "Was a nominee registered on the bank accounts?", "type": "boolean", "required": True},
                {"field": "has_insurance", "label": "Was there a life insurance policy?", "type": "boolean", "required": True},
                {"field": "insurance_age_months", "label": "How many months ago was the policy taken?", "type": "number", "required": False},
                {"field": "has_epf", "label": "Was deceased an EPF (Provident Fund) member?", "type": "boolean", "required": True},
                {"field": "has_pension", "label": "Was deceased receiving a government pension?", "type": "boolean", "required": True},
                {"field": "has_home_loan", "label": "Was there an outstanding home loan?", "type": "boolean", "required": True},
                {"field": "has_home_loan_insurance", "label": "Did the home loan have insurance (HLPP)?", "type": "boolean", "required": False},
                {"field": "will_exists", "label": "Did deceased leave a Will?", "type": "boolean", "required": True},
                {"field": "religion", "label": "Religion (affects inheritance law)",
                 "type": "select", "options": ["Hindu", "Muslim", "Christian", "Parsi", "Other"], "required": True},
                {"field": "spouse_alive", "label": "Is the spouse alive?", "type": "boolean", "required": True},
                {"field": "children_count", "label": "Number of children", "type": "number", "required": True},
                {"field": "minor_children_count", "label": "Number of minor children (under 18)", "type": "number", "required": True},
            ],
        }

    def _handle_intake(self, intake_data: dict) -> dict:
        """Process intake form and generate case profile."""
        self.case_profile = self.intake_agent.process(intake_data)
        self.state = "ACTIVE"

        # Generate initial check-in from Engagement Agent
        check_in = self.engagement_agent.process(
            "check_in", case_profile=self.case_profile
        )

        # Get the most urgent pending task
        urgent_tasks = [
            t for t in self.case_profile.get("tasks", [])
            if t.get("urgency") == "CRITICAL"
        ]
        first_task = urgent_tasks[0] if urgent_tasks else (
            self.case_profile.get("tasks", [{}])[0]
        )

        return {
            "agent": "Orchestrator → IntakeAgent + EngagementAgent",
            "state": "ACTIVE",
            "case_id": self.case_profile["case_id"],
            "complexity": self.case_profile["complexity_score"],
            "message": (
                f"{check_in['message']}\n\n"
                f"I have reviewed the details and identified "
                f"**{self.case_profile['total_tasks']} tasks** for you, "
                f"of which **{self.case_profile['urgent_tasks']} are urgent**.\n\n"
                f"Your case complexity is assessed as: **{self.case_profile['complexity_score']}**\n\n"
                f"The most important first step is:\n"
                f"→ **{first_task.get('name', 'Register the death')}**\n"
                f"   _{first_task.get('note', '')}_\n\n"
                f"You can ask me about any of these tasks and I will guide you "
                f"step by step with cited sources."
            ),
            "case_profile": self.case_profile,
            "iq_layers_active": {
                "Fabric IQ": "Estate complexity assessed using semantic model",
                "Foundry IQ": "Ready to retrieve cited guidance from knowledge base",
                "Work IQ": "Engagement timing will adapt to your capacity",
            },
        }

    def _route_to_agent(self, msg_lower: str, original_msg: str) -> dict:
        """
        Route the user message to the most appropriate sub-agent.
        Orchestrator decides routing based on keyword matching.
        """
        # Score each agent
        legal_score = sum(1 for kw in self.LEGAL_KEYWORDS if kw in msg_lower)
        financial_score = sum(1 for kw in self.FINANCIAL_KEYWORDS if kw in msg_lower)
        engagement_score = sum(1 for kw in self.ENGAGEMENT_KEYWORDS if kw in msg_lower)

        # Check for progress/summary requests
        if any(w in msg_lower for w in ["progress", "summary", "tasks", "pending", "how many"]):
            result = self.engagement_agent.process(
                "progress_summary", case_profile=self.case_profile
            )
            return result

        # Route to best matching agent
        scores = {"legal": legal_score, "financial": financial_score, "engagement": engagement_score}
        best_agent = max(scores, key=scores.get)

        if scores[best_agent] == 0 or best_agent == "engagement":
            # Default: check if it's a support request
            if any(w in msg_lower for w in ["support", "grief", "help", "resource", "helpline"]):
                return self.engagement_agent.process(
                    "support_resources", case_profile=self.case_profile
                )
            best_agent = "legal"  # Default to legal for unknown queries

        if best_agent == "legal":
            return self.legal_agent.process(original_msg, case_profile=self.case_profile)
        elif best_agent == "financial":
            return self.financial_agent.process(original_msg, case_profile=self.case_profile)
        else:
            return self.engagement_agent.process(
                "reminder", case_profile=self.case_profile,
                task=self._get_next_pending_task()
            )

    def _handle_follow_up(self, msg_lower: str, original_msg: str) -> dict:
        """Handle follow-up state — proactive check-ins."""
        # In follow-up state, default to engagement agent
        return self.engagement_agent.process(
            "reminder",
            case_profile=self.case_profile,
            task=self._get_next_pending_task(),
        )

    def _handle_complete(self) -> dict:
        return {
            "agent": "Orchestrator",
            "state": "COMPLETE",
            "message": (
                "All tasks in this case have been marked as complete. "
                "The estate administration process is now closed.\n\n"
                "We hope Saatvika was able to make this difficult journey a little easier. "
                "Our deepest condolences for your loss."
            ),
        }

    def _get_next_pending_task(self) -> Optional[dict]:
        """Get the highest-priority pending task from case profile."""
        if not self.case_profile:
            return None
        tasks = self.case_profile.get("tasks", [])
        return tasks[0] if tasks else None

    def _wrap_response(self, response: dict) -> dict:
        """Wrap all responses with metadata."""
        return {
            **response,
            "session": {
                "state": self.state,
                "case_id": self.case_profile.get("case_id") if self.case_profile else None,
                "messages_exchanged": len(self.conversation_history),
                "session_start": self.session_start,
            },
            "disclaimer": (
                "SAATVIKA provides information for guidance purposes only. "
                "All document citations are from synthetic demonstration materials. "
                "Please consult a qualified legal or financial professional for binding advice."
            ),
        }

    def get_full_task_list(self) -> dict:
        """Return the complete task list for the current case."""
        if not self.case_profile:
            return {"error": "No active case. Please complete intake first."}
        return {
            "case_id": self.case_profile["case_id"],
            "tasks": self.case_profile.get("tasks", []),
            "total": self.case_profile.get("total_tasks", 0),
        }

    def get_conversation_history(self) -> list[dict]:
        """Return full conversation history."""
        return self.conversation_history
