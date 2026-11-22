# CLAUDE.md

## Project overview

Tea Pet is a command-line chatbot about tea, built as a LangGraph **supervisor** multi-agent system using Gemini (via `langchain_google_genai`) and Google search (via SerpAPI). A supervisor routes each user request to one of three specialist agents.

## Setup & commands

- Python 3.13 virtualenv in `.venv/` (gitignored). Windows: `.venv\Scripts\Activate.ps1`
- Install deps: `pip install -r requirements.txt` (versions are pinned)
- `.env` (gitignored) must provide the API keys:
  - `GOOGLE_API_KEY` — read implicitly by `ChatGoogleGenerativeAI`
  - `SERPAPI_API_KEY` — read in `tools/google_tool.py`
- Run the chat CLI from the repo root: `python cli.py`
- Smoke-test that the agent graph compiles: `python agents/agents.py`
- Manually test the search tool (hits the real SerpAPI): `python "test scripts/test_google_tool.py"`
- There is no test framework, linter, or build step; `test scripts/` holds ad-hoc scripts, not pytest tests.

## Layout

- `cli.py` — interactive REPL. Builds the app with `create_all_agents()`, uses a fixed `thread_id` of `"1"`, and streams with `stream_mode='messages'`, `version='v2'`. It prints only `AIMessage`s that have text and no tool calls, and filters out handoff noise (text starting with `Transferring`, `Successfully transferred`, `Error:`). It loops forever with no exit command (the "Add exit condition" TODO is still open). A large commented-out older streaming loop sits at the bottom.
- `agents/agents.py` — all agent definitions. `create_all_agents()` returns the compiled supervisor graph.
  - Module-level singletons: `model` (`ChatGoogleGenerativeAI`, `gemini-3.5-flash-lite`), `checkpointer` (`InMemorySaver`), `store` (`InMemoryStore`). All state is in-memory and lost on exit.
  - Sub-agents, built with `langchain.agents.create_agent`: `tea_identifier`, `tea_researcher` (steeping time/temperature consensus), `tea_sommelier` (recommendations plus food pairings). Each has `google_tool` and a prompt inline in `agents.py`.
  - Supervisor: `langgraph_supervisor.create_supervisor` with `output_mode="full_history"`, `add_handoff_back_messages=True`, and a prompt telling it to delegate to one agent at a time and do no work itself.
  - `supervisor_pre_model_hook` — works around Gemini rejecting a conversation whose last message is an AIMessage without tool calls (the "model prefilling" error). It appends a synthetic HumanMessage via `llm_input_messages`. Keep this when changing the supervisor.
  - `sys.path.insert` at the top lets the file run directly; `cli.py` and the test script do the same or rely on the repo root being the cwd.
- `tools/google_tool.py` — `google_tool`, a `@tool` that runs a SerpAPI Google search and returns a JSON string of `{title, link, snippet}` for organic results. On an HTTP or timeout error it swallows the exception (printing only some) and returns `"[]"`, so agents fall back to general knowledge as their prompts say.

## Conventions & gotchas

- Agent behavior lives in the system prompts in `agents/agents.py`; changing behavior usually means editing those strings. Sub-agent prompts tell them not to call transfer tools and to answer in plain text.
- To add an agent: create it with `create_agent(..., name=...)` inside `create_all_agents()` and add it to the list passed to `create_supervisor`. Update the supervisor prompt so it knows what the agent does.
- To add a tool: put it in `tools/` as a `@tool` function with a docstring (used as the tool description) and pass it to the relevant agents.
- `tea_identifier` is meant to accept photos, but `cli.py` only sends text input.
- `README.md` is just a title stub.
