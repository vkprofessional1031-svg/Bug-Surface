import os
import instructor
from groq import Groq
from dotenv import load_dotenv

from agents.schemas import Plan
from agents.prompts.planner_prompt import PLANNER_SYSTEM_PROMPT, build_planner_user_prompt

load_dotenv()

client = instructor.from_groq(Groq(api_key=os.environ["GROQ_API_KEY"]))

def run_planner(issue_text: str, file_contents: dict) -> Plan:
    plan = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        response_model=Plan,
        messages=[
            {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
            {"role": "user", "content": build_planner_user_prompt(issue_text, file_contents)},
        ],
    )
    return plan
