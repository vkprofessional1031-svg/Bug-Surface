import os
import instructor
from groq import Groq
from dotenv import load_dotenv

from agents.schemas import ReviewVerdict
from agents.prompts.reviewer_prompt import REVIEWER_SYSTEM_PROMPT, build_reviewer_user_prompt

load_dotenv()

client = instructor.from_groq(
    Groq(api_key=os.environ["GROQ_API_KEY"]), mode=instructor.Mode.JSON
)

def run_reviewer(issue_text: str, diff_text: str) -> ReviewVerdict:
    return client.chat.completions.create(
        model="openai/gpt-oss-120b",
        response_model=ReviewVerdict,
        max_retries=3,
        messages=[
            {"role": "system", "content": REVIEWER_SYSTEM_PROMPT},
            {"role": "user", "content": build_reviewer_user_prompt(issue_text, diff_text)},
        ],
    )
