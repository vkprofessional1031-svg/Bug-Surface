import os
import instructor
from groq import Groq
from dotenv import load_dotenv

from agents.schemas import CoderOutput
from agents.prompts.coder_prompt import (
    CODER_SYSTEM_PROMPT,
    build_coder_user_prompt,
    build_memory_context,
)

load_dotenv()

client = instructor.from_groq(
    Groq(api_key=os.environ["GROQ_API_KEY"]), mode=instructor.Mode.JSON
)

def run_coder(plan, file_contents: dict, test_feedback: str = None, memory_lessons: list = None) -> CoderOutput:
    user_prompt = build_coder_user_prompt(plan, file_contents, test_feedback)
    user_prompt += build_memory_context(memory_lessons or [])

    result = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        response_model=CoderOutput,
        max_retries=3,
        messages=[
            {"role": "system", "content": CODER_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    return result
