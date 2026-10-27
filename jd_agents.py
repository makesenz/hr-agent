"""AutoGen agents that draft, review and promote a job description.

A writer agent drafts the JD, a reviewer agent checks it, and the two take turns
until the reviewer replies APPROVE (or the round limit is hit). A separate agent
then turns the approved JD into a LinkedIn hiring post.
"""

import os
from dataclasses import dataclass

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

MODEL = "gpt-4o-mini"
APPROVE_WORD = "APPROVE"
# Writer + reviewer turns, so 6 messages = at most 3 drafts.
MAX_MESSAGES = 6

WRITER_SYSTEM = """You are a senior HR content writer at a corporate company.
You write clear, professional, inclusive job descriptions in Markdown.

Always return the COMPLETE job description using exactly this structure:

# <Job Title>
**Department:** ... | **Level:** ... | **Employment type:** ... | **Work mode:** ... | **Location:** ... | **Reports to:** ...

## About the Role
2-3 sentences on the purpose and impact of the role.

## Key Responsibilities
5-7 bullet points, each starting with an action verb.

## Requirements
5-7 bullet points with skills and experience realistic for the seniority level.

## Nice to Have
2-4 bullet points.

## Why Join Us
2-3 bullet points about growth, learning and team culture, kept generic.

Rules:
- Use only the role details you are given. Infer typical responsibilities and skills
  from the job title, department and seniority.
- Never invent salary figures, benefits, company names, products or awards.
- Use gender-neutral, inclusive language. Do not mention age, "young", "native speaker",
  "rockstar", "ninja" or similar.
- Match experience requirements to the seniority (for example, an Intern needs no prior work experience).
- When the reviewer gives feedback, apply every point and return the full revised JD.
- Output only the JD in Markdown, with no commentary before or after it."""

REVIEWER_SYSTEM = f"""You are an HR compliance and quality reviewer at a corporate company.
You review job descriptions written by the HR writer.

Check the latest JD for:
1. Consistency with the role details (title, department, level, employment type, work mode, location, reports to).
2. Inclusive, bias-free language (no gendered terms, no age hints, no unnecessary requirements).
3. Experience and skill requirements that are realistic for the seniority level.
4. Invented facts such as salary numbers, benefits, company names or products. These are not allowed.
5. The required structure: About the Role, Key Responsibilities, Requirements, Nice to Have, Why Join Us.
6. Clarity and a professional tone.

If the JD passes every check, reply with only the word {APPROVE_WORD}.
Otherwise reply with a short numbered list of specific fixes. Do not rewrite the JD yourself
and do not include the word {APPROVE_WORD} in your feedback."""

LINKEDIN_SYSTEM = """You are an employer-branding specialist.
You turn job descriptions into short LinkedIn hiring posts.
Write 80-150 words: a hook line, 3-4 short bullet highlights, the work mode and location,
a clear call to apply, and 3-5 relevant hashtags. Keep it professional, warm and inclusive.
Use at most 3 emojis. Never invent salary, benefits or company names.
Output only the post text."""


@dataclass
class RoleInputs:
    job_title: str
    department: str
    seniority: str
    employment_type: str
    work_mode: str
    location: str
    reports_to: str

    def as_brief(self) -> str:
        return (
            f"- Job title: {self.job_title}\n"
            f"- Department: {self.department}\n"
            f"- Seniority level: {self.seniority}\n"
            f"- Employment type: {self.employment_type}\n"
            f"- Work mode: {self.work_mode}\n"
            f"- Location: {self.location}\n"
            f"- Reports to: {self.reports_to}"
        )


@dataclass
class JDResult:
    jd_markdown: str
    approved: bool
    transcript: list[tuple[str, str]]


def _model_client() -> OpenAIChatCompletionClient:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to the .env file.")
    return OpenAIChatCompletionClient(model=MODEL, api_key=api_key)


async def generate_jd(role: RoleInputs) -> JDResult:
    model_client = _model_client()
    try:
        writer = AssistantAgent(
            name="jd_writer", model_client=model_client, system_message=WRITER_SYSTEM
        )
        reviewer = AssistantAgent(
            name="jd_reviewer", model_client=model_client, system_message=REVIEWER_SYSTEM
        )
        termination = TextMentionTermination(
            APPROVE_WORD, sources=["jd_reviewer"]
        ) | MaxMessageTermination(MAX_MESSAGES + 1)  # +1 for the task message
        team = RoundRobinGroupChat([writer, reviewer], termination_condition=termination)

        task = f"Write a job description for this role:\n{role.as_brief()}"
        result = await team.run(task=task)
    finally:
        await model_client.close()

    transcript = [
        (m.source, m.content) for m in result.messages if isinstance(m, TextMessage)
    ]
    drafts = [content for source, content in transcript if source == "jd_writer"]
    approved = bool(transcript) and transcript[-1][0] == "jd_reviewer" and (
        APPROVE_WORD in transcript[-1][1]
    )
    return JDResult(jd_markdown=drafts[-1] if drafts else "", approved=approved, transcript=transcript)


async def generate_linkedin_post(jd_markdown: str) -> str:
    model_client = _model_client()
    try:
        agent = AssistantAgent(
            name="linkedin_writer", model_client=model_client, system_message=LINKEDIN_SYSTEM
        )
        result = await agent.run(task=f"Write a LinkedIn hiring post for this job description:\n\n{jd_markdown}")
    finally:
        await model_client.close()
    return result.messages[-1].content
