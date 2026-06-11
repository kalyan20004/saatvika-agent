"""
SAATVIKA — Engagement & Grief Support Agent
=============================================
The most human-facing agent. Sends compassionate, context-aware task reminders
and surfaces grief counselling + legal aid resources.

IQ Layer: Work IQ — understands temporal work context to adapt reminder timing and tone.
In MOCK_MODE: uses time-of-day and days-since-death for adaptive behavior.
"""
from datetime import datetime, time
from typing import Optional

import config


class EngagementAgent:
    """
    Keeps the family on track with compassionate, adaptive reminders.
    Adjusts communication style based on how recently the death occurred.
    Never sends reminders during likely difficult periods.
    """

    # Sensitive periods (days after death where tone must be most gentle)
    ACUTE_GRIEF_DAYS = 7      # First week — extreme sensitivity
    EARLY_GRIEF_DAYS = 30     # First month — high sensitivity
    ACTIVE_GRIEF_DAYS = 90    # First 3 months — medium sensitivity

    # Work-context-aware windows (Work IQ simulation)
    PREFERRED_REMINDER_HOURS = range(9, 18)  # 9 AM – 6 PM
    AVOID_HOURS = [*range(0, 8), *range(21, 24)]  # Late night / early morning

    TONE_MAP = {
        "ACUTE":    "gentle",
        "EARLY":    "supportive",
        "ACTIVE":   "encouraging",
        "SUSTAINED": "motivating",
    }

    def __init__(self):
        pass

    def process(self, action: str, case_profile: Optional[dict] = None,
                task: Optional[dict] = None) -> dict:
        """
        Main entry. Routes to appropriate engagement action.

        Args:
            action: One of 'reminder', 'support_resources', 'check_in', 'progress_summary'
            case_profile: Case context from IntakeAgent
            task: Specific task context (for reminders)

        Returns:
            dict with message, tone, timing_advice, resources
        """
        days_since = case_profile.get("days_since_death", 30) if case_profile else 30
        grief_stage = self._assess_grief_stage(days_since)
        tone = self.TONE_MAP[grief_stage]
        timing = self._assess_timing()

        if action == "reminder":
            return self._send_reminder(task, case_profile, grief_stage, tone, timing)
        elif action == "support_resources":
            return self._get_support_resources(grief_stage, case_profile)
        elif action == "check_in":
            return self._check_in(case_profile, grief_stage, tone, timing)
        elif action == "progress_summary":
            return self._progress_summary(case_profile, grief_stage)
        else:
            return self._check_in(case_profile, grief_stage, tone, timing)

    def _assess_grief_stage(self, days: int) -> str:
        if days <= self.ACUTE_GRIEF_DAYS:
            return "ACUTE"
        elif days <= self.EARLY_GRIEF_DAYS:
            return "EARLY"
        elif days <= self.ACTIVE_GRIEF_DAYS:
            return "ACTIVE"
        return "SUSTAINED"

    def _assess_timing(self) -> dict:
        """
        Work IQ simulation: assess whether this is a good time to send a reminder.
        In real Work IQ integration, this would check the user's calendar and focus windows.
        """
        now = datetime.now()
        hour = now.hour
        day_of_week = now.weekday()  # 0=Monday, 6=Sunday

        is_good_time = hour in self.PREFERRED_REMINDER_HOURS
        is_weekend = day_of_week >= 5

        return {
            "current_hour": hour,
            "is_weekend": is_weekend,
            "is_good_time_to_send": is_good_time,
            "recommended_send_time": "10:00 AM – 12:00 PM on weekdays",
            "work_iq_note": (
                "Work IQ (simulated): Reminder timing adapted to avoid "
                "early morning, late night, and likely difficult periods."
            ),
        }

    def _send_reminder(self, task: Optional[dict], case: Optional[dict],
                       stage: str, tone: str, timing: dict) -> dict:
        """Generate a compassionate, context-aware task reminder."""

        deceased = case.get("deceased_name", "your loved one") if case else "your loved one"
        task_name = task.get("name", "this task") if task else "the next task"
        task_urgency = task.get("urgency", "MEDIUM") if task else "MEDIUM"

        # Tone-adapted opening phrases
        openers = {
            "gentle": [
                "We know this is an incredibly difficult time.",
                "Please take all the time you need.",
                "There is no rush, and we are here with you.",
            ],
            "supportive": [
                "We hope you are finding moments of peace.",
                "You are doing an amazing job managing everything.",
                "One step at a time — that is all anyone can ask.",
            ],
            "encouraging": [
                "You have already taken some important steps.",
                "Each task you complete brings closure a little closer.",
                "You are not alone in this.",
            ],
            "motivating": [
                "You have come a long way in managing this difficult process.",
                "You are in the home stretch.",
                "Almost there — the finish line is in sight.",
            ],
        }

        import random
        opener = random.choice(openers.get(tone, openers["supportive"]))

        # Urgency-adapted message
        if task_urgency == "CRITICAL":
            urgency_note = (
                f"⚠️ This task is time-sensitive. Completing it soon will prevent "
                "complications later."
            )
        elif task_urgency == "HIGH":
            urgency_note = "This task is important and should be done in the next week or two."
        else:
            urgency_note = "This task can be done at a pace that feels comfortable for you."

        should_send = timing.get("is_good_time_to_send", True)

        return {
            "agent": "Engagement & Grief Support Agent",
            "iq_layer": "Work IQ (simulated) — time-context adapted reminder",
            "action": "reminder",
            "grief_stage": stage,
            "tone": tone,
            "message": (
                f"{opener}\n\n"
                f"When you feel ready, the next step is:\n\n"
                f"**{task_name}**\n\n"
                f"{urgency_note}\n\n"
                f"If you have questions about this step, just ask Saatvika — "
                f"we will guide you through it with full citations."
            ),
            "should_send_now": should_send,
            "timing_advice": timing,
            "grief_resources_link": "Ask Saatvika: 'Show me grief support resources'",
        }

    def _get_support_resources(self, stage: str, case: Optional[dict]) -> dict:
        """Return grief counselling and legal aid resources."""
        state = case.get("state", "") if case else ""

        state_resources = {
            "Andhra Pradesh": {
                "legal_aid": "Andhra Pradesh State Legal Services Authority — apslsa.org",
                "helpline": "iCall: 9152987821",
            },
            "Telangana": {
                "legal_aid": "Telangana State Legal Services Authority — tslsa.org",
                "helpline": "iCall: 9152987821",
            },
            "Tamil Nadu": {
                "legal_aid": "Tamil Nadu State Legal Services Authority — tnslsa.tn.gov.in",
                "helpline": "Snehi: 044-24640050",
            },
            "Karnataka": {
                "legal_aid": "Karnataka State Legal Services Authority — kslsa.kar.nic.in",
                "helpline": "NIMHANS: 080-46110007",
            },
            "Maharashtra": {
                "legal_aid": "Maharashtra State Legal Services Authority — nalsa.gov.in",
                "helpline": "iCall: 9152987821",
            },
        }

        resources = state_resources.get(state, {
            "legal_aid": "National Legal Services Authority (NALSA) — nalsa.gov.in",
            "helpline": "iCall (TISS): 9152987821 | Vandrevala Foundation: 1860-2662-345",
        })

        return {
            "agent": "Engagement & Grief Support Agent",
            "iq_layer": "Work IQ (simulated) — contextual resource surfacing",
            "action": "support_resources",
            "grief_stage": stage,
            "message": (
                "It is completely normal to feel overwhelmed. Here are some resources "
                "that can help — both emotionally and practically."
            ),
            "mental_health_helplines": [
                {"name": "iCall (TISS)", "number": "9152987821", "hours": "Mon–Sat, 8 AM–10 PM"},
                {"name": "Vandrevala Foundation", "number": "1860-2662-345", "hours": "24/7"},
                {"name": "NIMHANS Helpline", "number": "080-46110007", "hours": "Mon–Sat"},
            ],
            "legal_aid": resources.get("legal_aid", "National Legal Services Authority — nalsa.gov.in"),
            "state_specific_helpline": resources.get("helpline", "iCall: 9152987821"),
            "ngos": [
                "HelpAge India: 1800-180-1253",
                "Red Cross India: indianredcross.org",
            ],
            "self_care_reminder": (
                "Please remember: one task per day is enough. Eat regularly, rest when you can, "
                "and do not make major financial decisions in the first few months."
            ),
            "disclaimer": "SYNTHETIC RESOURCE LIST — For demonstration only.",
        }

    def _check_in(self, case: Optional[dict], stage: str, tone: str, timing: dict) -> dict:
        """Gentle check-in message."""
        days = case.get("days_since_death", 0) if case else 0
        tasks_total = case.get("total_tasks", 0) if case else 0

        stage_messages = {
            "ACUTE": (
                "We just want you to know Saatvika is here whenever you are ready. "
                "There is no pressure. The most urgent step when you have strength "
                "is registering the death — but even that can wait a day or two."
            ),
            "EARLY": (
                f"It has been {days} days. We know time feels strange right now. "
                f"When you are ready, there are {tasks_total} tasks to work through — "
                "but you do not need to do them all at once."
            ),
            "ACTIVE": (
                f"You have been managing this for {days} days now. "
                "Each step you complete matters. Would you like a summary of "
                "what is still pending?"
            ),
            "SUSTAINED": (
                "You have come a long way. Let us review what is remaining "
                "and make a plan to finish strong."
            ),
        }

        return {
            "agent": "Engagement & Grief Support Agent",
            "iq_layer": "Work IQ (simulated)",
            "action": "check_in",
            "grief_stage": stage,
            "tone": tone,
            "message": stage_messages.get(stage, "We are here to help whenever you are ready."),
            "timing_advice": timing,
        }

    def _progress_summary(self, case: Optional[dict], stage: str) -> dict:
        """Summarize progress and pending tasks."""
        if not case:
            return {"message": "No active case found. Please start by describing your situation."}

        total = case.get("total_tasks", 0)
        urgent = case.get("urgent_tasks", 0)
        days = case.get("days_since_death", 0)
        name = case.get("deceased_name", "your loved one")

        # Build the task list string
        task_list_str = ""
        tasks = case.get("tasks", [])
        if tasks:
            task_list_str = "\n\n**Pending Tasks (in order of priority):**\n"
            for i, t in enumerate(tasks):
                urgency_icon = "🔴 " if t.get("urgency") == "CRITICAL" else "🟡 " if t.get("urgency") == "HIGH" else "🔵 "
                task_list_str += f"{i+1}. {urgency_icon}**{t.get('name')}**\n"
            task_list_str += "\n_(Type the exact name of any task above to get a step-by-step guide!)_"

        return {
            "agent": "Engagement & Grief Support Agent",
            "iq_layer": "Work IQ (simulated)",
            "action": "progress_summary",
            "grief_stage": stage,
            "summary": {
                "deceased_name": name,
                "days_since_death": days,
                "total_tasks": total,
                "urgent_tasks_remaining": urgent,
                "estimated_completion_days": case.get("estimated_completion_days", 90),
            },
            "message": (
                f"Here is where things stand for {name}'s estate:\n\n"
                f"• Total tasks identified: {total}\n"
                f"• Tasks marked CRITICAL: {urgent}\n"
                f"• Days since passing: {days}\n"
                f"• Estimated time to complete all tasks: "
                f"{case.get('estimated_completion_days', 90)} days"
                f"{task_list_str}"
            ),
        }
