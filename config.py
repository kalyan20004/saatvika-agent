"""
SAAtvika Configuration Module
Loads environment variables and provides configuration to all agents.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
KNOWLEDGE_BASE_DIR = BASE_DIR / os.getenv("KNOWLEDGE_BASE_PATH", "knowledge-base")
DATA_DIR = BASE_DIR / "data" / "synthetic"

# Azure AI Foundry configuration
AZURE_AI_PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT", "")
AZURE_AI_MODEL_DEPLOYMENT = os.getenv("AZURE_AI_MODEL_DEPLOYMENT", "gpt-4o")

# App configuration
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"

# Mock mode — runs without Azure credentials using local knowledge base
MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"

# IQ Layer feature flags
USE_FOUNDRY_IQ = bool(AZURE_AI_PROJECT_ENDPOINT) and not MOCK_MODE
USE_FABRIC_IQ = bool(AZURE_AI_PROJECT_ENDPOINT) and not MOCK_MODE
USE_WORK_IQ = bool(AZURE_AI_PROJECT_ENDPOINT) and not MOCK_MODE

def get_config_summary() -> dict:
    """Returns a safe configuration summary (no secrets)."""
    return {
        "mock_mode": MOCK_MODE,
        "foundry_iq_enabled": USE_FOUNDRY_IQ,
        "fabric_iq_enabled": USE_FABRIC_IQ,
        "work_iq_enabled": USE_WORK_IQ,
        "knowledge_base_path": str(KNOWLEDGE_BASE_DIR),
        "azure_endpoint_configured": bool(AZURE_AI_PROJECT_ENDPOINT),
    }
