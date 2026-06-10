# 🪔 Saatvika — AI Agent for Grief & Estate Navigation

> **Microsoft Agents League Hackathon 2026** | Track: 🧠 Reasoning Agents | Built by Nukala Naga Kalyan

---

## 🎬 Demo Video
> 📹 **[Watch the 2-minute Demo on YouTube](#)** ← *(Update this link before submission)*

---

## 💡 The Problem

When someone dies in India, their family faces over **30+ administrative tasks** across legal, financial, and government systems — all while in the depths of grief. They must obtain death certificates, notify banks, claim EPF and insurance, cancel pensions, transfer property, and more.

Most families have **no idea where to start, what order to follow, or what documents they need**. A single mistake — like missing the 21-day death registration window — can trigger months of legal complications.

**Saatvika** fills this gap. It is a multi-agent AI system that guides bereaved Indian families through every step — with grounded, cited answers from official sources. **Never hallucinated.**

---

## 🤖 What Saatvika Does

- 📋 **Creates a personalised, urgency-ranked task plan** based on the family's specific assets, state, and situation
- ⚖️ **Guides legal steps** — death certificates, probate, succession, property mutation — with state-specific instructions
- 💰 **Guides financial claims** — bank notification, LIC/insurance, EPF, pension, home loans — with cited checklists
- 💙 **Provides compassionate reminders** — adapted to the family's grief stage, never intrusive
- 🆘 **Surfaces grief support resources** — mental health helplines, legal aid NGOs, state-specific contacts

---

## 🏗️ Architecture

```
                    ┌─────────────────────────────────────┐
                    │           USER / FAMILY              │
                    └──────────────────┬──────────────────┘
                                       │
                                       ▼
                    ┌─────────────────────────────────────┐
                    │         🎯 ORCHESTRATOR              │
                    │   State Machine: INTAKE → ACTIVE     │
                    │         → FOLLOW_UP → COMPLETE       │
                    └─────┬──────────┬──────────┬─────────┘
                          │          │          │
              ┌───────────┘   ┌──────┘   ┌─────┘
              ▼               ▼          ▼
   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐
   │ 🟢 LEGAL     │  │ 🟡 FINANCIAL │  │ 🔴 ENGAGEMENT        │
   │    AGENT     │  │    AGENT     │  │    AGENT             │
   │              │  │              │  │                      │
   │ Foundry IQ ↓ │  │Foundry IQ ↓  │  │ Work IQ ↓            │
   │ Death Cert   │  │ Bank/LIC     │  │ Grief-stage aware    │
   │ Probate      │  │ EPF/Pension  │  │ Compassionate tone   │
   │ Property     │  │ Home Loan    │  │ Adaptive timing      │
   └──────────────┘  └──────────────┘  └──────────────────────┘
              ↑               ↑
   ┌──────────────────────────────────┐
   │         🔵 INTAKE AGENT          │
   │                                  │
   │         Fabric IQ ↓              │
   │  Collects family situation       │
   │  Maps to estate semantic model   │
   │  Generates urgency-ranked tasks  │
   └──────────────────────────────────┘
```

---

## 💡 Microsoft IQ Integration

### ⚡ Foundry IQ — Knowledge Retrieval Layer
**Used by:** Legal Agent, Financial Agent

Foundry IQ is the grounded knowledge retrieval layer. Saatvika's Legal and Financial agents query a knowledge base of **10 synthetic guidance documents** covering India's death administration process:

- `india_death_certificate_guide.md` — State-wise registration, deadlines, forms
- `india_bank_notification_guide.md` — RBI guidelines on deceased accounts
- `india_insurance_claim_checklist.md` — LIC + private insurer claim process
- `india_epf_withdrawal_guide.md` — EPF Form 20, EDLI, EPS pension
- `india_property_transfer_guide.md` — Mutation, succession, probate states
- `india_probate_guide.md` — High Court procedure, costs, timelines
- `grief_support_resources.md` — Helplines, NGOs, mental health contacts
- `legal_heir_certificate_guide.md` — Tehsildar process, state portals
- `pension_cancellation_guide.md` — CCS Rules, family pension amounts
- `synthetic_case_examples.md` — 3 fictional demonstration cases

**Every agent answer includes a source citation.** No free-text legal advice without attribution.

### 🧩 Fabric IQ — Semantic Estate Model
**Used by:** Intake Agent, Financial Agent

Fabric IQ provides the semantic foundation for estate reasoning. The Intake Agent uses a semantic model to:
- Map the deceased's situation (employment type, assets, state, family) to a typed task list
- Apply complexity rules (e.g., *"no_nominee_bank AND bank_accounts > 0 → Succession Certificate required"*)
- Estimate completion timelines based on complexity scores
- Resolve entity relationships: `deceased → assets → tasks → urgency → agent`

### 💼 Work IQ — Work Context Adaptation
**Used by:** Engagement Agent

Work IQ informs the Engagement Agent about when and how to communicate. The agent:
- Assesses **grief stage** (Acute / Early / Active / Sustained) based on days since death
- Adapts **tone** (gentle / supportive / encouraging / motivating)
- Avoids reminders during **likely difficult periods** (late night, grief anniversaries)
- Surfaces **state-specific legal aid** and **mental health helplines**

---

## 🔄 Multi-Agent Flow

```
1. Family describes their situation via Intake Form
2. Intake Agent (Fabric IQ) → produces urgency-ranked JSON case profile
3. Orchestrator transitions to ACTIVE state
4. Family asks: "How do I get a death certificate?"
5. Orchestrator routes → Legal Agent
6. Legal Agent (Foundry IQ) → retrieves india_death_certificate_guide.md
7. Returns: cited answer + source + state-specific notes
8. Family asks: "How do I claim EPF?"
9. Orchestrator routes → Financial Agent
10. Financial Agent (Foundry IQ + Fabric IQ) → retrieves epf guide + semantic urgency
11. Returns: cited steps + actionable checklist + warnings
12. Engagement Agent (Work IQ) → sends compassionate reminders at appropriate times
13. Orchestrator → COMPLETE when all tasks marked done
```

---

## 🚀 Setup & Running Locally

### Prerequisites
- Python 3.10+
- (Optional) Azure subscription for Foundry IQ in production mode

### Step 1: Clone and Install
```bash
git clone https://github.com/kalyan20004/saatvika-agent
cd saatvika-agent
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### Step 2: Configure Environment
```bash
# Copy the example env file
cp .env.example .env

# Edit .env — set MOCK_MODE=true to run without Azure (default)
# To use Azure Foundry IQ: add your AZURE_AI_PROJECT_ENDPOINT
```

### Step 3: Run the Server
```bash
python main.py
```

### Step 4: Open the App
```
http://localhost:8000
```

API Documentation available at: `http://localhost:8000/api/docs`

---

## 🗂️ Project Structure

```
saatvika-agent/
├── main.py                    # FastAPI backend — all API routes
├── config.py                  # Environment configuration
├── requirements.txt
├── .env.example               # Environment template (commit this, not .env)
├── .gitignore
│
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py        # State machine coordinator
│   ├── intake_agent.py        # Fabric IQ — case profiling
│   ├── legal_agent.py         # Foundry IQ — legal guidance
│   ├── financial_agent.py     # Foundry IQ + Fabric IQ — financial claims
│   └── engagement_agent.py    # Work IQ — compassionate engagement
│
├── knowledge-base/            # Foundry IQ knowledge sources (10 synthetic docs)
│   ├── india_death_certificate_guide.md
│   ├── india_bank_notification_guide.md
│   ├── india_insurance_claim_checklist.md
│   ├── india_epf_withdrawal_guide.md
│   ├── india_property_transfer_guide.md
│   ├── india_probate_guide.md
│   ├── grief_support_resources.md
│   ├── legal_heir_certificate_guide.md
│   ├── pension_cancellation_guide.md
│   └── synthetic_case_examples.md
│
├── data/
│   └── synthetic/
│       ├── case_profiles.json         # Fabric IQ — sample case data
│       └── estate_semantic_model.json # Fabric IQ — entity + complexity rules
│
└── frontend/
    ├── index.html             # Single-page app
    ├── style.css              # Premium dark UI
    └── app.js                 # Chat + intake + task management
```

---

## 📊 Judging Criteria Alignment

| Criterion | How Saatvika Addresses It |
|---|---|
| **Accuracy & Relevance (25%)** | All answers cite source documents. Legal Agent never returns free-text without citation. Foundry IQ grounds every response. |
| **Reasoning & Multi-step (25%)** | 5-agent orchestration with state machine. Complex routing: intake → classification → specialist agent → grounded retrieval → cited response |
| **Creativity & Originality (15%)** | Grief & estate navigation is a uniquely human, underserved domain. No other team will likely build this. |
| **User Experience (15%)** | Warm, empathetic UI. Compassionate language. One-click quick actions. Task priority view. |
| **Reliability & Safety (20%)** | No hallucination by design (citation-only). Guardrails on sensitive grief content. Synthetic data only. |

---

## ⚠️ Synthetic Data Disclaimer

**All data in this project is entirely synthetic and for demonstration purposes only.**

- All case examples use fictional names and IDs (e.g., `CASE-2024-001`, `L-1001`, `EMP-001`)
- No real personal information, PII, or customer data is included
- Knowledge base documents are synthetic guides referencing publicly available law frameworks
- Case profiles, semantic models, and example datasets are fabricated for demonstration

This project complies fully with the Agents League Hackathon security and data guidelines.

---

## 🔐 Security

- API keys and credentials stored in `.env` (never committed — see `.gitignore`)
- MOCK_MODE=true runs entirely without cloud credentials
- No real personal data accepted or stored
- All session data is in-memory only (no persistence)

---

## 👤 About the Builder

**Nukala Naga Kalyan** — B.Tech CSE 2026, Amrita Vishwa Vidyapeetham  
SAP HackFest 2025 Regional Winner | IEEE Xplore Published Researcher | CGPA 9.51/10

Built Saatvika for families navigating one of life's most difficult moments — because administrative chaos should never compound grief.

- GitHub: [github.com/kalyan20004](https://github.com/kalyan20004)
- LinkedIn: [linkedin.com/in/nukala-naga-kalyan-286b002b4](https://www.linkedin.com/in/nukala-naga-kalyan-286b002b4/)

---

## 📄 License

MIT License — see LICENSE file.
