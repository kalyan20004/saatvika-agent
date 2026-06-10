"""
SAATVIKA — Legal & Documents Agent
====================================
Handles legal queries about death certificates, succession, probate,
Legal Heir Certificates, and property mutation.

IQ Layer: Foundry IQ — retrieves grounded, cited answers from the knowledge base.
In MOCK_MODE: searches local markdown files in /knowledge-base.
"""
import re
from pathlib import Path
from typing import Optional

import config


class LegalAgent:
    """
    Answers legal questions about estate processes, always with source citations.
    Never returns free-text legal advice without citing a source document.
    """

    DOMAIN_KEYWORDS = {
        "death_certificate": [
            "death certificate", "death registration", "register death",
            "municipal", "gram panchayat", "21 days", "crsorgi"
        ],
        "legal_heir": [
            "legal heir", "heir certificate", "varisu", "vaarisu",
            "tehsildar", "revenue", "relationship proof"
        ],
        "succession": [
            "succession certificate", "letters of administration",
            "district court", "movable property", "succession"
        ],
        "probate": [
            "probate", "will", "executor", "high court", "testator",
            "validate will", "estate administration"
        ],
        "property": [
            "property", "mutation", "dakhil kharij", "land", "house",
            "flat", "apartment", "plot", "real estate", "meebhoomi",
            "dharani", "mahabhulekh"
        ],
        "grief": [
            "grief", "counselling", "mental health", "support", "helpline",
            "sad", "difficult", "overwhelmed", "help", "ngo"
        ],
    }

    def __init__(self):
        self.knowledge_base = self._load_knowledge_base()

    def _load_knowledge_base(self) -> dict[str, str]:
        """Load all knowledge base documents into memory."""
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

    def process(self, query: str, case_profile: Optional[dict] = None) -> dict:
        """
        Process a legal query and return a grounded, cited answer.

        Args:
            query: The family's question (e.g., "How do I get a death certificate?")
            case_profile: Optional case context from IntakeAgent

        Returns:
            dict with answer, citation, source_document, confidence
        """
        query_lower = query.lower()
        domain = self._classify_query(query_lower)
        doc_name, doc_content = self._retrieve_document(domain)

        if not doc_content:
            return self._fallback_response(query)

        # Extract the most relevant section from the document
        answer_section = self._extract_relevant_section(query_lower, doc_content)

        # Personalize with case context if available
        personalized_note = ""
        if case_profile:
            personalized_note = self._personalize(query_lower, domain, case_profile)

        return {
            "agent": "Legal & Documents Agent",
            "iq_layer": "Foundry IQ — Local Knowledge Base (Mock Mode)",
            "query": query,
            "domain": domain,
            "answer": answer_section,
            "personalized_note": personalized_note,
            "citation": {
                "source_document": doc_name,
                "document_path": f"knowledge-base/{doc_name}.md",
                "disclaimer": "SYNTHETIC DOCUMENT — For demonstration only. Not real legal advice.",
            },
            "confidence": "HIGH" if domain != "general" else "MEDIUM",
            "follow_up_suggestions": self._suggest_follow_ups(domain, case_profile),
        }

    def _classify_query(self, query: str) -> str:
        """Match query to a legal domain."""
        scores = {}
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in query)
            scores[domain] = score

        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "general"

    def _retrieve_document(self, domain: str) -> tuple[str, str]:
        """Return (doc_name, doc_content) for the matched domain."""
        domain_to_doc = {
            "death_certificate": "india_death_certificate_guide",
            "legal_heir": "legal_heir_certificate_guide",
            "succession": "india_probate_guide",
            "probate": "india_probate_guide",
            "property": "india_property_transfer_guide",
            "grief": "grief_support_resources",
        }
        doc_name = domain_to_doc.get(domain, "india_death_certificate_guide")
        return doc_name, self.knowledge_base.get(doc_name, "")

    def _extract_relevant_section(self, query: str, content: str) -> str:
        """
        Extract the most relevant section from a markdown document
        based on the query keywords.
        """
        sections = re.split(r"\n##+ ", content)
        if not sections:
            return content[:800]

        best_section = sections[0]
        best_score = 0
        query_words = set(query.split())

        for section in sections[1:]:
            section_lower = section.lower()
            score = sum(1 for word in query_words if word in section_lower and len(word) > 3)
            if score > best_score:
                best_score = score
                best_section = section

        # Return heading + content, max 600 chars to keep response concise
        result = "## " + best_section.strip()
        if len(result) > 700:
            result = result[:700] + "\n\n_[See full document for complete details]_"
        return result

    def _personalize(self, query: str, domain: str, case: dict) -> str:
        """Add state/situation-specific notes using the case profile."""
        notes = []
        state = case.get("state", "")
        days = case.get("days_since_death", 0)

        if domain == "death_certificate":
            if days > 30:
                notes.append(
                    f"⚠️ For {case.get('deceased_name', 'the deceased')}'s case: "
                    f"Death occurred {days} days ago. You will need an Executive Magistrate/SDM order."
                )
            elif days > 21:
                notes.append(
                    f"⚠️ Death occurred {days} days ago — late fee applies but no court order needed."
                )

        if domain == "property" and state in ["Maharashtra", "Tamil Nadu", "West Bengal"]:
            notes.append(
                f"⚠️ For {state}: Probate is mandatory before property mutation. "
                "File a Probate Petition in the District Court first."
            )

        if domain == "probate" and not case.get("will_exists", True):
            notes.append(
                "ℹ️ Since there is no Will: apply for a Succession Certificate "
                "(not Probate) for movable assets, and Legal Heir Certificate for property."
            )

        return " ".join(notes)

    def _suggest_follow_ups(self, domain: str, case: Optional[dict]) -> list[str]:
        """Suggest related questions the family might have next."""
        suggestions_map = {
            "death_certificate": [
                "How many certified copies of the death certificate do I need?",
                "How do I notify the bank after getting the death certificate?",
                "How do I apply for a Legal Heir Certificate?",
            ],
            "legal_heir": [
                "What documents do I need for property mutation?",
                "Is a Succession Certificate different from a Legal Heir Certificate?",
                "How long does property mutation take?",
            ],
            "property": [
                "What if there are multiple legal heirs who disagree?",
                "Do I need to pay stamp duty for inherited property?",
                "What happens to the home loan after death?",
            ],
            "probate": [
                "How long does probate take?",
                "Do I need a lawyer for probate?",
                "What is a Succession Certificate and when do I need it?",
            ],
            "grief": [
                "Can you help me list all the tasks I need to complete?",
                "Where can I get free legal help?",
                "What should I prioritize first?",
            ],
        }
        return suggestions_map.get(domain, [
            "How do I get a death certificate?",
            "What are the most urgent tasks?",
        ])

    def _fallback_response(self, query: str) -> dict:
        return {
            "agent": "Legal & Documents Agent",
            "iq_layer": "Foundry IQ — Knowledge Base Not Loaded",
            "query": query,
            "domain": "general",
            "answer": (
                "I wasn't able to find a specific document for your question. "
                "Please start with the most urgent step: registering the death "
                "at your local Municipal Corporation or Gram Panchayat within 21 days."
            ),
            "citation": {
                "source_document": "general",
                "disclaimer": "For demonstration only. Not real legal advice.",
            },
            "confidence": "LOW",
            "follow_up_suggestions": [
                "How do I register a death?",
                "What documents do I need for a death certificate?",
            ],
        }
