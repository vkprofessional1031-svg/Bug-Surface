PLANNER_SYSTEM_PROMPT = """You are a senior software engineer planning a bug fix.
Given an issue description and relevant file contents, produce a plan.
Be specific about root cause -- don't guess vaguely.
List concrete, ordered subtasks a developer could follow directly."""

def build_planner_user_prompt(issue_text: str, file_contents: dict) -> str:
    files_section = "\n\n".join(
        f"--- {path} ---\n{content}" for path, content in file_contents.items()
    )
    return f"""Issue:
{issue_text}

Relevant files:
{files_section}

Produce a plan to fix this issue."""
