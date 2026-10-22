# PRD Genie: AI-Powered Product Documentation Assistant

A multi-agent AI pipeline that turns meeting transcripts, product briefs and
stakeholder notes into structured PRDs, epics, features and user stories,
without inventing requirements that were never stated.

> Capstone project for *Applied Agentic AI for PMs/TPMs*. 

## Status
🚧 In progress

## Planned architecture
Sequential pipeline with an input-sufficiency gate:

Requirement Extractor → Gate → PRD Generator → Story Breakdown → Gap Analyzer

## Tech stack
| Component | Choice |
|---|---|
| Workflow | LangFlow |
| LLM | GPT-4o-mini |
| Observability | Langfuse |
| Output | Markdown |

## Repository contents (coming soon)
- `workflows/`: LangFlow workflow exports
- `prompts/`: agent system prompts
- `evals/`: baseline dataset, scoring script, test results
- `docs/`: architecture, ideation, program charter, reflection
