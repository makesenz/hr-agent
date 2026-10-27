import asyncio
import os
import sys

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

# Load OPENAI_API_KEY from the .env file next to this script.
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# "5 lines" is ambiguous to a model, so the task spells out the exact shape:
# one title line followed by exactly five numbered single-sentence lines.
TASK = (
    "Write a job description for a Junior Python Developer. "
    "Format: the first line is just the job title 'Junior Python Developer'. "
    "Then write exactly 5 numbered lines (1. to 5.), each a single sentence. "
    "Do not add any introduction, closing remarks, headings, or extra lines."
)


async def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        sys.exit("OPENAI_API_KEY is not set. Add it to the .env file before running this script.")

    model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", api_key=api_key)
    agent = AssistantAgent(
        name="hr_assistant",
        model_client=model_client,
        system_message="You are an HR assistant.",
    )

    try:
        await Console(agent.run_stream(task=TASK))
    finally:
        # An unclosed client leaves the script hanging.
        await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
