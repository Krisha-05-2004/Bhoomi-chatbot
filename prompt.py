from pathlib import Path
from langchain.prompts import PromptTemplate

PROMPTS_DIR = Path(r"K:\DOCUMENTS ABOUT AGRICULTURE\prompt")

def load_prompt(file_name: str) -> str:
    file_path = PROMPTS_DIR / file_name
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()

main_prompt_str = load_prompt("main_prompt.txt")

MAIN_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=f"""{main_prompt_str}

Context:
{{context}}

Question:
{{question}}
"""
)
