# AutoGen HR Assistant (Week 5 · Day 1)

This folder has two parts:

1. **`hr_agent.py`**: the assignment. A single AutoGen `AssistantAgent` with the system message
   `"You are an HR assistant."` that writes a 5-line job description for a Junior Python Developer.
2. **`app.py`**: a Streamlit JD generator for corporate HR teams, built on a two-agent AutoGen team.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then paste your key into .env
```

## Run the assignment script

```bash
python hr_agent.py
```

## Run the JD Generator app

```bash
streamlit run app.py
```

Fill in the role basics: job title, department, seniority, employment type, work mode,
location and reports to. The app then:

1. **jd_writer** drafts a structured JD (About the Role, Key Responsibilities, Requirements,
   Nice to Have, Why Join Us).
2. **jd_reviewer** checks the draft against the inputs, inclusive-language rules,
   seniority-appropriate requirements, and invented facts such as salary or benefits.
   It sends numbered fixes back to the writer, or replies `APPROVE`.
3. They take turns in a `RoundRobinGroupChat` until the reviewer approves (at most 3 drafts).
4. **linkedin_writer** turns the approved JD into a short LinkedIn hiring post.

## Files

| File | Purpose |
| --- | --- |
| `hr_agent.py` | Assignment script (single agent, console output) |
| `jd_agents.py` | Writer, reviewer and LinkedIn agents, and the team logic |
| `app.py` | Streamlit UI |
| `.env.example` | Template for `OPENAI_API_KEY` |

## Notes

- The API key is loaded from `.env` with `python-dotenv` and never hard-coded.
  `.env` is git-ignored; `.env.example` is the template.
- Model clients are always closed after each run, so nothing hangs.
