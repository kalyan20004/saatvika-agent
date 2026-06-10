"""
SAATVIKA — FastAPI Backend
===========================
Exposes REST API endpoints for the frontend to interact with all agents.
Runs in Mock Mode by default (no Azure credentials needed to start).
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any
from pathlib import Path
import uvicorn

import config
from agents import Orchestrator

# ─────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────
app = FastAPI(
    title="SAATVIKA — AI Agent for Grief & Estate Navigation",
    description=(
        "A multi-agent AI system that guides bereaved Indian families through "
        "every administrative, legal, and emotional step after a death. "
        "Grounded in cited knowledge — Foundry IQ, Fabric IQ, and Work IQ."
    ),
    version="1.0.0",
    docs_url="/api/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────
# Session Store (in-memory, per session)
# ─────────────────────────────────────────
sessions: dict[str, Orchestrator] = {}


def get_or_create_session(session_id: str) -> Orchestrator:
    if session_id not in sessions:
        sessions[session_id] = Orchestrator()
    return sessions[session_id]


# ─────────────────────────────────────────
# Pydantic Models
# ─────────────────────────────────────────
class ChatRequest(BaseModel):
    session_id: str
    message: str
    intake_data: Optional[dict[str, Any]] = None


class IntakeFormData(BaseModel):
    session_id: str
    deceased_name: str
    date_of_death: str
    state: str
    city: str
    employment_type: str
    has_property: bool
    has_bank_accounts: bool
    bank_account_count: int = 0
    has_nominee_bank: bool = False
    has_insurance: bool = False
    insurance_age_months: int = 99
    has_epf: bool = False
    has_pension: bool = False
    has_home_loan: bool = False
    has_home_loan_insurance: bool = False
    will_exists: bool = False
    religion: str = "Hindu"
    spouse_alive: bool = True
    children_count: int = 0
    minor_children_count: int = 0


# ─────────────────────────────────────────
# API Routes
# ─────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def serve_frontend():
    """Serve the main frontend HTML."""
    frontend_path = Path(__file__).parent / "frontend" / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    return {"message": "SAATVIKA API is running. Visit /api/docs for API documentation."}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "SAATVIKA",
        "version": "1.0.0",
        "config": config.get_config_summary(),
        "active_sessions": len(sessions),
    }


@app.get("/api/welcome/{session_id}")
async def welcome(session_id: str):
    """Get the welcome message and intake form structure."""
    orch = get_or_create_session(session_id)
    response = orch.process_message("start")
    return response


@app.post("/api/intake")
async def submit_intake(data: IntakeFormData):
    """Submit the intake form to create a case profile."""
    orch = get_or_create_session(data.session_id)
    intake_dict = data.model_dump(exclude={"session_id"})
    response = orch.process_message(
        message="Submitting intake form",
        intake_data=intake_dict
    )
    return response


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Send a message to the Orchestrator.
    Routes to LegalAgent, FinancialAgent, or EngagementAgent as appropriate.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    orch = get_or_create_session(request.session_id)
    response = orch.process_message(
        message=request.message,
        intake_data=request.intake_data,
    )
    return response


@app.get("/api/tasks/{session_id}")
async def get_tasks(session_id: str):
    """Get the full prioritized task list for the current session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    orch = sessions[session_id]
    return orch.get_full_task_list()


@app.get("/api/history/{session_id}")
async def get_history(session_id: str):
    """Get full conversation history for a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    orch = sessions[session_id]
    return {"session_id": session_id, "history": orch.get_conversation_history()}


@app.post("/api/support/{session_id}")
async def get_support(session_id: str):
    """Get grief support and legal aid resources for the current case."""
    orch = get_or_create_session(session_id)
    case = orch.case_profile
    result = orch.engagement_agent.process("support_resources", case_profile=case)
    return result


@app.get("/api/knowledge-base")
async def list_knowledge_base():
    """List all knowledge base documents (Foundry IQ sources)."""
    kb_path = config.KNOWLEDGE_BASE_DIR
    if not kb_path.exists():
        return {"documents": []}
    docs = [
        {
            "name": f.stem,
            "filename": f.name,
            "size_bytes": f.stat().st_size,
            "iq_layer": "Foundry IQ",
        }
        for f in kb_path.glob("*.md")
    ]
    return {
        "total_documents": len(docs),
        "iq_layer": "Foundry IQ — Local Knowledge Base (Mock Mode)",
        "documents": docs,
    }


@app.delete("/api/session/{session_id}")
async def end_session(session_id: str):
    """End and clear a session."""
    if session_id in sessions:
        del sessions[session_id]
    return {"message": f"Session {session_id} ended.", "status": "cleared"}


# ─────────────────────────────────────────
# Static Files (Frontend)
# ─────────────────────────────────────────
frontend_dir = Path(__file__).parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


# ─────────────────────────────────────────
# Run
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  SAATVIKA — AI Agent for Grief & Estate Navigation")
    print("  Microsoft Agents League Hackathon 2026")
    print("="*60)
    print(f"  Mode: {'MOCK (Local KB)' if config.MOCK_MODE else 'AZURE (Foundry IQ)'}")
    print(f"  Server: http://{config.APP_HOST}:{config.APP_PORT}")
    print(f"  API Docs: http://localhost:{config.APP_PORT}/api/docs")
    print("="*60 + "\n")

    uvicorn.run(
        "main:app",
        host=config.APP_HOST,
        port=config.APP_PORT,
        reload=config.DEBUG_MODE,
    )
