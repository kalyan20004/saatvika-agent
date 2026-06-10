"""
SAATVIKA — Financial & Estate Agent
=====================================
Handles financial queries: bank accounts, insurance claims, EPF, pension,
home loans, and estate financial planning.

IQ Layer: Foundry IQ (knowledge retrieval) + Fabric IQ (entity relationships)
In MOCK_MODE: uses local knowledge base + semantic model JSON.
"""
import json
from pathlib import Path
from typing import Optional

import config


class FinancialAgent:
    """
    Answers financial estate questions with cited guidance from the knowledge base.
    Specializes in bank notifications, insurance, EPF, and pension procedures.
    """

    DOMAIN_KEYWORDS = {
        "bank": [
            "bank", "account", "nominee", "savings", "fd", "fixed deposit",
            "locker", "transfer", "freeze", "rbi", "claim form", "sbi", "hdfc"
        ],
        "insurance": [
            "insurance", "lic", "policy", "premium", "claim", "death benefit",
            "irda", "irdai", "hdfc life", "sbi life", "bajaj", "max life"
        ],
        "epf": [
            "epf", "provident fund", "pf", "edli", "epfo", "form 20",
            "form 10", "form 5", "uan", "gratuity", "employer"
        ],
        "pension": [
            "pension", "ppo", "family pension", "railway pension", "government pension",
            "nps", "retirement", "monthly pension", "overpayment", "pda"
        ],
        "home_loan": [
            "home loan", "housing loan", "hlpp", "mortgage", "emi",
            "outstanding loan", "loan insurance", "property loan"
        ],
    }

    def __init__(self):
        self.knowledge_base = self._load_knowledge_base()
        self.semantic_model = self._load_semantic_model()

    def _load_knowledge_base(self) -> dict[str, str]:
        docs = {}
        kb_path = config.KNOWLEDGE_BASE_DIR
        if not kb_path.exists():
            return docs
        for md_file in kb_path.glob("*.md"):
            try:
                docs[md_file.stem] = md_file.read_text(encoding="utf-8")
            except Exception:
                pass
        return docs

    def _load_semantic_model(self) -> dict:
        model_path = config.DATA_DIR / "estate_semantic_model.json"
        try:
            with open(model_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def process(self, query: str, case_profile: Optional[dict] = None) -> dict:
        """
        Process a financial estate query and return a grounded, cited answer.

        Args:
            query: Family's financial question
            case_profile: Optional case context from IntakeAgent

        Returns:
            dict with answer, citation, actionable checklist
        """
        query_lower = query.lower()
        domain = self._classify_domain(query_lower)
        doc_name, doc_content = self._get_document(domain)
        answer = self._extract_answer(query_lower, doc_content, domain)
        checklist = self._generate_checklist(domain, case_profile)
        warnings = self._generate_warnings(domain, case_profile)

        return {
            "agent": "Financial & Estate Agent",
            "iq_layer": "Foundry IQ + Fabric IQ Semantic Model",
            "query": query,
            "domain": domain,
            "answer": answer,
            "actionable_checklist": checklist,
            "warnings": warnings,
            "citation": {
                "source_document": doc_name,
                "document_path": f"knowledge-base/{doc_name}.md",
                "disclaimer": "SYNTHETIC DOCUMENT — For demonstration only. Not real financial advice.",
            },
            "fabric_iq_context": self._get_fabric_context(domain),
            "follow_up_suggestions": self._suggest_follow_ups(domain),
        }

    def _classify_domain(self, query: str) -> str:
        scores = {d: sum(1 for kw in kws if kw in query)
                  for d, kws in self.DOMAIN_KEYWORDS.items()}
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "bank"

    def _get_document(self, domain: str) -> tuple[str, str]:
        domain_to_doc = {
            "bank": "india_bank_notification_guide",
            "insurance": "india_insurance_claim_checklist",
            "epf": "india_epf_withdrawal_guide",
            "pension": "pension_cancellation_guide",
            "home_loan": "india_property_transfer_guide",
        }
        doc_name = domain_to_doc.get(domain, "india_bank_notification_guide")
        return doc_name, self.knowledge_base.get(doc_name, "")

    def _extract_answer(self, query: str, content: str, domain: str) -> str:
        """Extract a relevant answer from document content."""
        if not content:
            return self._default_answer(domain)

        # Find the most relevant paragraph
        paragraphs = content.split("\n\n")
        query_words = set(w for w in query.split() if len(w) > 3)
        best_para = ""
        best_score = 0

        for para in paragraphs:
            score = sum(1 for w in query_words if w in para.lower())
            if score > best_score and len(para.strip()) > 50:
                best_score = score
                best_para = para

        if not best_para:
            best_para = paragraphs[1] if len(paragraphs) > 1 else content[:600]

        return best_para.strip()[:700]

    def _generate_checklist(self, domain: str, case: Optional[dict]) -> list[str]:
        """Generate domain-specific action checklist."""
        checklists = {
            "bank": [
                "Gather all bank passbooks / account statements of deceased",
                "Visit the home branch of each bank in person",
                "Submit written notice of death with Death Certificate",
                "Request immediate account freeze",
                "Fill the bank's claim form (nominee or legal heir)",
                "Submit nominee / heir ID proof and cancelled cheque",
                "Follow up at 15-day mark (RBI mandates settlement within 15 days for < ₹5 lakh)",
                "Confirm account closure after fund transfer",
            ],
            "insurance": [
                "Locate all insurance policy documents (physical/digital)",
                "Note each policy's servicing branch or insurer app",
                "Intimate insurer in writing within 30 days of death",
                "Collect death claim form from insurer's branch/website",
                "Attach: Death Certificate + original policy bond + claimant ID",
                "For LIC: also attach Form 3784 (non-accidental)",
                "Obtain claim reference number",
                "Follow up at 30-day mark (IRDAI mandates settlement in 30 days)",
            ],
            "epf": [
                "Get deceased member's UAN from employer or epfindia.gov.in",
                "Download Form 20 (EPF claim) + Form 5-IF (EDLI claim) + Form 10-D (EPS pension)",
                "Get employer attestation on Form 20",
                "Attach Death Certificate + nominee's Aadhaar + PAN + passbook",
                "If minor nominee: obtain Guardianship Certificate first",
                "Submit at EPFO regional office OR employer submits online",
                "EDLI benefit (up to ₹7 lakh) is separate — file Form 5-IF simultaneously",
                "Track on epfindia.gov.in — settlement within 30 days",
            ],
            "pension": [
                "Notify pension disbursing bank (PDA) in writing immediately",
                "Submit Death Certificate to bank to stop pension credits",
                "Notify last employer / Head of Office",
                "Submit PPO (Pension Payment Order) booklet",
                "Fill Form 14 (Central Govt) or state equivalent for family pension",
                "Attach: Marriage Certificate / Birth Certificates for relationship proof",
                "Check if overpayment occurred — be prepared to refund",
                "Family pension starts within 1–3 months of complete submission",
            ],
            "home_loan": [
                "Notify the lending bank of the death immediately",
                "Check loan documents for HLPP (Home Loan Protection Plan) insurance",
                "If HLPP exists: file insurance claim to settle outstanding loan",
                "If no HLPP: heir inherits both property AND loan — do not miss EMIs",
                "Request bank to issue No Objection Certificate (NOC) once loan settles",
                "Do NOT sell property until loan is formally closed",
            ],
        }
        return checklists.get(domain, [])

    def _generate_warnings(self, domain: str, case: Optional[dict]) -> list[str]:
        """Generate context-aware warnings."""
        warnings = []
        if domain == "pension":
            warnings.append(
                "⚠️ URGENT: Pension overpayment must be refunded. Check bank statements from date of death."
            )
        if domain == "insurance" and case:
            ins_age = case.get("insurance_age_months", 99)
            if ins_age < 36:
                warnings.append(
                    "⚠️ EARLY CLAIM: Policy is less than 3 years old. Insurer will conduct "
                    "a detailed investigation (60–90 days). Be patient and keep all documents."
                )
        if domain == "bank" and case and not case.get("has_nominee_bank"):
            warnings.append(
                "⚠️ NO NOMINEE: For large amounts (>₹1 lakh), you will need a "
                "Succession Certificate from the District Court. This takes 3–6 months."
            )
        return warnings

    def _get_fabric_context(self, domain: str) -> dict:
        """
        Fabric IQ context: returns semantic entity relationship data
        relevant to the domain.
        """
        task_types = self.semantic_model.get("entities", {}).get("task_types", [])
        domain_task_map = {
            "bank": "BANK_NOTIFICATION",
            "insurance": "INSURANCE_CLAIM",
            "epf": "EPF_CLAIM",
            "pension": "PENSION_CANCEL",
            "home_loan": "BANK_NOTIFICATION",
        }
        task_id = domain_task_map.get(domain)
        for task in task_types:
            if task.get("id") == task_id:
                return {
                    "semantic_entity": task_id,
                    "urgency": task.get("urgency"),
                    "dependencies": task.get("dependencies", []),
                    "week": task.get("week"),
                    "note": "Retrieved from Fabric IQ Estate Semantic Model (Mock)",
                }
        return {"semantic_entity": domain, "note": "Fabric IQ entity not found"}

    def _suggest_follow_ups(self, domain: str) -> list[str]:
        suggestions = {
            "bank": [
                "What happens to a Fixed Deposit after death?",
                "Can I access the bank locker without the account holder?",
                "What is the RBI deadline for settling bank claims?",
            ],
            "insurance": [
                "What if no nominee is registered on the policy?",
                "How do I file a PMJJBY (government scheme) claim?",
                "What if the insurer rejects the claim?",
            ],
            "epf": [
                "What is the EDLI insurance benefit and how much is it?",
                "How do I claim gratuity from the employer?",
                "What if the employer is not cooperating with the EPF claim?",
            ],
            "pension": [
                "How much is family pension for central government employees?",
                "What is the enhanced family pension period?",
                "How do I claim NPS (National Pension System) benefits?",
            ],
            "home_loan": [
                "What happens if I miss EMI payments during this period?",
                "How do I transfer the home loan to my name?",
                "What if the home loan has no insurance?",
            ],
        }
        return suggestions.get(domain, [])

    def _default_answer(self, domain: str) -> str:
        defaults = {
            "bank": "Please notify each bank branch in writing with the Death Certificate. Most banks will freeze the account and process the claim within 15 days per RBI guidelines.",
            "insurance": "Please contact the insurance company's nearest branch or use their online portal to initiate a death claim. Gather the policy bond, death certificate, and claim forms.",
            "epf": "Contact the employer for the deceased member's UAN and file Form 20 with EPFO. The EDLI benefit of up to ₹7 lakh is available separately.",
            "pension": "Notify the pension disbursing bank immediately to stop pension credits. Then contact the last employer to initiate family pension.",
            "home_loan": "Notify the lending bank of the death. Check for home loan insurance (HLPP) that may settle the outstanding amount.",
        }
        return defaults.get(domain, "Please consult a certified legal or financial professional for guidance.")
