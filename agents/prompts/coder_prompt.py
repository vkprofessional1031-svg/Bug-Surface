CODER_SYSTEM_PROMPT = """You are a careful software engineer fixing a bug.
You will be given a plan and the current contents of relevant files.
Output the COMPLETE new content for each file that needs to change --
not a diff, not a snippet, the entire file with your fix applied.
Preserve all existing code that isn't related to the fix.
Do not change formatting or unrelated lines."""

def build_coder_user_prompt(plan, file_contents: dict, test_feedback: str = None) -> str:
    files_section = "\n\n".join(
        f"--- {path} ---\n{content}" for path, content in file_contents.items()
    )
    feedback_section = f"\n\nPrevious attempt failed with:\n{test_feedback}" if test_feedback else ""
    return f"""Plan:
Root cause: {plan.root_cause_hypothesis}
Subtasks: {plan.subtasks}

Current file contents:
{files_section}
{feedback_section}

Produce the complete fixed file contents."""
