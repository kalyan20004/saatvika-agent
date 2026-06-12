# 🪔 SAATVIKA — AI Guidance for Families Navigating Grief

**Saatvika** is an empathetic, multi-agent AI orchestrator designed to guide bereaved families through the overwhelming legal and financial bureaucracy following the loss of a loved one. By combining compassionate engagement with hard, cited legal facts, Saatvika turns an impossible burden into a manageable, step-by-step journey.

## 🚀 Key Features

* **Multi-Agent Orchestrator:** Seamlessly routes user queries between specialized Legal, Financial, and Grief Support AI agents without breaking the conversation flow.
* **Fabric IQ (Contextual Intelligence):** Evaluates estate complexity dynamically using an intake form (factoring in religion, property, and minors to adjust inheritance laws).
* **Work IQ (Dynamic State Tracking):** Generates a prioritized, numbered checklist. Intercepts queries to provide 5-step pin-to-pin guides. Updates the UI in real-time when users complete a task.
* **Foundry IQ (Grounded Citations):** Completely eliminates legal hallucinations by strictly citing official government sources for all administrative advice.

## 💻 Tech Stack

* **Backend:** Python 3.x, FastAPI, Uvicorn
* **Frontend:** Vanilla JavaScript, HTML5, Custom CSS (Glassmorphism, CSS Variables, Flexbox/Grid)
* **Architecture:** Micro-agent routing pattern with centralized state management.

## 🛠️ Running Locally

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/saatvika-agent.git
   cd saatvika-agent
   ```

2. **Set up a virtual environment (Optional but recommended):**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install fastapi uvicorn pydantic
   ```

4. **Start the server:**
   ```bash
   python main.py
   ```

5. **Access the application:**
   Open your browser and navigate to `http://localhost:8000`

## 🔒 Demo Credentials
* **Username:** admin
* **Password:** saatvik123

---
*Built with ❤️ for the Microsoft AI Hackathon.*
