"""
SAATVIKA — Intake Agent
=======================
Collects case details from the grieving family and produces a structured,
urgency-ranked task list. Acts as the first point of contact.

IQ Layer: Fabric IQ — resolves estate complexity level using semantic model.
In MOCK_MODE: uses local estate_semantic_model.json for task generation.
"""
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

import config


class IntakeAgent:
    """
    Collects information about the deceased and their estate,
    then generates a prioritized task plan for the family.
    """

    COMPLEXITY_WEIGHTS = {
        "has_property": 2,
        "no_will": 2,
        "multiple_heirs": 1,
        "no_nominee_bank": 3,
        "insurance_early_claim": 2,
        "probate_state": 3,
        "commercial_property": 2,
        "home_loan": 1,
        "minor_children": 2,
    }

    PROBATE_MANDATORY_STATES = ["Maharashtra", "Tamil Nadu", "West Bengal"]

    def __init__(self):
        self.semantic_model = self._load_semantic_model()

    def _load_semantic_model(self) -> dict:
        """Load Fabric IQ semantic model (local JSON in mock mode)."""
        model_path = config.DATA_DIR / "estate_semantic_model.json"
        try:
            with open(model_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"entities": {"task_types": [], "complexity_rules": []}}

    def process(self, intake_data: dict) -> dict:
        """
        Main entry point. Takes family input and returns a structured case profile
        with urgency-ranked tasks.

        Args:
            intake_data: dict with keys:
                - deceased_name: str
                - date_of_death: str (YYYY-MM-DD)
                - state: str
                - city: str
                - employment_type: str (government/private/self_employed/retired)
                - has_property: bool
                - has_bank_accounts: bool
                - bank_account_count: int
                - has_nominee_bank: bool
                - has_insurance: bool
                - insurance_age_months: int (optional)
                - has_epf: bool
                - has_pension: bool
                - has_home_loan: bool
                - has_home_loan_insurance: bool
                - will_exists: bool
                - religion: str (Hindu/Muslim/Christian/Other)
                - spouse_alive: bool
                - children_count: int
                - minor_children_count: int

        Returns:
            case_profile: dict with case_id, complexity, tasks[]
        """
        case_id = self._generate_case_id()
        complexity_score, complexity_flags = self._assess_complexity(intake_data)
        tasks = self._generate_task_list(intake_data, complexity_flags)
        days_since_death = self._days_since_death(intake_data.get("date_of_death", ""))

        case_profile = {
            "case_id": case_id,
            "iq_layer": "Fabric IQ — Estate Semantic Model",
            "deceased_name": intake_data.get("deceased_name", "Unknown"),
            "date_of_death": intake_data.get("date_of_death", ""),
            "days_since_death": days_since_death,
            "state": intake_data.get("state", ""),
            "city": intake_data.get("city", ""),
            "complexity_score": complexity_score,
            "complexity_flags": complexity_flags,
            "tasks": tasks,
            "total_tasks": len(tasks),
            "urgent_tasks": len([t for t in tasks if t["urgency"] == "CRITICAL"]),
            "estimated_completion_days": self._estimate_completion(complexity_score),
            "generated_at": datetime.now().isoformat(),
            "synthetic_data_disclaimer": (
                "This case profile is for demonstration purposes. "
                "All recommendations are illustrative only."
            ),
        }

        return case_profile

    def _generate_case_id(self) -> str:
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"SAATVIKA-{ts}"

    def _days_since_death(self, date_str: str) -> int:
        if not date_str:
            return 0
        try:
            dod = datetime.strptime(date_str, "%Y-%m-%d")
            return (datetime.now() - dod).days
        except ValueError:
            return 0

    def _assess_complexity(self, d: dict) -> tuple[str, list[str]]:
        """
        Assess estate complexity using Fabric IQ semantic rules.
        Returns (complexity_level, list_of_flags).
        """
        flags = []
        score = 0

        if d.get("has_property"):
            flags.append("has_property")
            score += self.COMPLEXITY_WEIGHTS["has_property"]

        if not d.get("will_exists"):
            flags.append("no_will")
            score += self.COMPLEXITY_WEIGHTS["no_will"]

        children = d.get("children_count", 0)
        if children > 1 or (children >= 1 and d.get("spouse_alive")):
            flags.append("multiple_heirs")
            score += self.COMPLEXITY_WEIGHTS["multiple_heirs"]

        if d.get("has_bank_accounts") and not d.get("has_nominee_bank"):
            flags.append("no_nominee_bank")
            score += self.COMPLEXITY_WEIGHTS["no_nominee_bank"]

        ins_age = d.get("insurance_age_months", 99)
        if d.get("has_insurance") and ins_age < 36:
            flags.append("insurance_early_claim")
            score += self.COMPLEXITY_WEIGHTS["insurance_early_claim"]

        if d.get("state") in self.PROBATE_MANDATORY_STATES and d.get("has_property"):
            flags.append("probate_state")
            score += self.COMPLEXITY_WEIGHTS["probate_state"]

        if d.get("commercial_property"):
            flags.append("commercial_property")
            score += self.COMPLEXITY_WEIGHTS["commercial_property"]

        if d.get("has_home_loan"):
            flags.append("home_loan")
            score += self.COMPLEXITY_WEIGHTS["home_loan"]

        if d.get("minor_children_count", 0) > 0:
            flags.append("minor_children")
            score += self.COMPLEXITY_WEIGHTS["minor_children"]

        if score <= 3:
            level = "LOW"
        elif score <= 7:
            level = "MEDIUM"
        elif score <= 12:
            level = "HIGH"
        else:
            level = "VERY_HIGH"

        return level, flags

    def _generate_task_list(self, d: dict, flags: list[str]) -> list[dict]:
        """Generate urgency-ranked task list based on the family's situation."""
        tasks = []
        state = d.get("state", "")

        # Task 1: Death Certificate — ALWAYS first and CRITICAL
        days_since = self._days_since_death(d.get("date_of_death", ""))
        cert_urgency = "CRITICAL" if days_since < 21 else "HIGH"
        cert_note = ""
        if days_since > 30:
            cert_note = "⚠️ Death occurred >30 days ago — requires Executive Magistrate/SDM order."
        elif days_since > 21:
            cert_note = "⚠️ Death occurred >21 days ago — late fee applies."

        tasks.append({
            "task_id": "T-001",
            "name": "Register Death & Obtain Death Certificate",
            "category": "legal",
            "urgency": cert_urgency,
            "week": 1,
            "agent": "Legal & Documents Agent",
            "dependencies": [],
            "note": cert_note or "Obtain at least 10 certified copies.",
            "iq_source": "Foundry IQ — india_death_certificate_guide.md",
        })

        # Task 2: Bank notification — if has bank accounts
        if d.get("has_bank_accounts"):
            note = ""
            if not d.get("has_nominee_bank"):
                note = "⚠️ No nominee registered — Succession Certificate from court required for large amounts."
            tasks.append({
                "task_id": "T-002",
                "name": f"Notify {d.get('bank_account_count', 1)} Bank Account(s) of Death",
                "category": "financial",
                "urgency": "HIGH",
                "week": 1,
                "agent": "Financial & Estate Agent",
                "dependencies": ["T-001"],
                "note": note or "Submit Death Certificate + claim form at each bank branch.",
                "iq_source": "Foundry IQ — india_bank_notification_guide.md",
            })

        # Task 3: Insurance claim
        if d.get("has_insurance"):
            ins_urgency = "HIGH"
            ins_note = ""
            if d.get("insurance_age_months", 99) < 36:
                ins_note = "⚠️ Early claim — insurer will investigate for 60–90 days. File immediately."
            tasks.append({
                "task_id": "T-003",
                "name": "File Life Insurance Death Claim",
                "category": "financial",
                "urgency": ins_urgency,
                "week": 2,
                "agent": "Financial & Estate Agent",
                "dependencies": ["T-001"],
                "note": ins_note or "Collect Form 3784 (LIC) or equivalent from insurer.",
                "iq_source": "Foundry IQ — india_insurance_claim_checklist.md",
            })

        # Task 4: EPF claim
        if d.get("has_epf"):
            epf_note = ""
            if d.get("minor_children_count", 0) > 0:
                epf_note = "⚠️ Minor nominee — obtain Guardianship Certificate before filing."
            tasks.append({
                "task_id": "T-004",
                "name": "File EPF / EDLI Death Claim",
                "category": "financial",
                "urgency": "HIGH",
                "week": 2,
                "agent": "Financial & Estate Agent",
                "dependencies": ["T-001"],
                "note": epf_note or "File Form 20 + Form 5-IF (EDLI) + Form 10-D/10-C.",
                "iq_source": "Foundry IQ — india_epf_withdrawal_guide.md",
            })

        # Task 5: Pension (if government employee/retired)
        if d.get("has_pension"):
            tasks.append({
                "task_id": "T-005",
                "name": "Cancel Deceased Pension & Start Family Pension",
                "category": "financial",
                "urgency": "CRITICAL",
                "week": 1,
                "agent": "Financial & Estate Agent",
                "dependencies": ["T-001"],
                "note": "Notify pension disbursing bank AND last employer immediately. Overpayment must be refunded.",
                "iq_source": "Foundry IQ — pension_cancellation_guide.md",
            })

        # Task 6: Legal Heir Certificate
        if d.get("has_property") or not d.get("has_nominee_bank"):
            tasks.append({
                "task_id": "T-006",
                "name": "Obtain Legal Heir Certificate",
                "category": "legal",
                "urgency": "HIGH",
                "month": 1,
                "agent": "Legal & Documents Agent",
                "dependencies": ["T-001"],
                "note": "Apply at Tehsildar/Revenue Office. Takes 15–30 days.",
                "iq_source": "Foundry IQ — legal_heir_certificate_guide.md",
            })

        # Task 7: Property Mutation
        if d.get("has_property"):
            prop_note = ""
            if state in self.PROBATE_MANDATORY_STATES:
                prop_note = f"⚠️ {state}: Probate may be required before mutation."
            tasks.append({
                "task_id": "T-007",
                "name": "Property Mutation (Dakhil Kharij)",
                "category": "property",
                "urgency": "MEDIUM",
                "month": 2,
                "agent": "Legal & Documents Agent",
                "dependencies": ["T-001", "T-006"],
                "note": prop_note or "Apply at local Revenue Office with Legal Heir Certificate.",
                "iq_source": "Foundry IQ — india_property_transfer_guide.md",
            })

        # Task 8: Probate (if mandatory state)
        if state in self.PROBATE_MANDATORY_STATES and d.get("has_property"):
            tasks.append({
                "task_id": "T-008",
                "name": f"File Probate Petition — {state} (Mandatory)",
                "category": "legal",
                "urgency": "HIGH",
                "month": 1,
                "agent": "Legal & Documents Agent",
                "dependencies": ["T-001"],
                "note": f"Probate is mandatory for property in {state}. File petition in District Court.",
                "iq_source": "Foundry IQ — india_probate_guide.md",
            })

        # Task 9: Home Loan
        if d.get("has_home_loan"):
            loan_note = ""
            if d.get("has_home_loan_insurance"):
                loan_note = "✅ Home loan insurance (HLPP) detected — claim may settle outstanding loan."
            else:
                loan_note = "⚠️ No home loan insurance — heir inherits loan liability. Notify bank immediately."
            tasks.append({
                "task_id": "T-009",
                "name": "Home Loan Notification & HLPP Claim",
                "category": "financial",
                "urgency": "CRITICAL",
                "week": 1,
                "agent": "Financial & Estate Agent",
                "dependencies": ["T-001"],
                "note": loan_note,
                "iq_source": "Foundry IQ — india_property_transfer_guide.md",
            })

        # Sort by urgency: CRITICAL → HIGH → MEDIUM → LOW
        urgency_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        tasks.sort(key=lambda t: urgency_order.get(t.get("urgency", "LOW"), 3))
        return tasks

    def _estimate_completion(self, complexity: str) -> int:
        estimates = {"LOW": 60, "MEDIUM": 90, "HIGH": 120, "VERY_HIGH": 180}
        return estimates.get(complexity, 90)
