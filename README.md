# tea-pet

Tea Pet is a command-line chatbot that helps you enjoy tea. A supervisor agent listens to your request and hands it to the specialist agent best suited to answer.

## How to use

1. Clone the repo:
   ```
   git clone <repo-url>
   ```
2. Create a `.env` file in the root of the repo (see [.env file format](#env-file-format) below).
3. Open a terminal pointed at the repo directory:
   ```
   cd tea-pet
   ```
4. (Recommended) Create and activate a virtual environment, then install the dependencies:
   ```
   python -m venv .venv
   .venv\Scripts\Activate.ps1      # Windows PowerShell
   source .venv/bin/activate       # macOS / Linux
   pip install -r requirements.txt
   ```
5. Run the script:
   ```
   python cli.py
   ```
6. Type a question at the `Ask a question:` prompt and press Enter. Press `Ctrl+C` to quit.

## .env file format

Create a file named `.env` in the repo root with the following variables:

```
GOOGLE_API_KEY=your-google-gemini-api-key
SERPAPI_API_KEY=your-serpapi-api-key
```

| Variable | Purpose |
| --- | --- |
| `GOOGLE_API_KEY` | Gemini API key used by the language model that powers every agent. |
| `SERPAPI_API_KEY` | [SerpAPI](https://serpapi.com/) key used by the Google search tool. |

The `.env` file is gitignored, so your keys won't be committed.

## What the tool can do

Tea Pet is made up of a supervisor and three specialist agents. The supervisor only routes requests and does no work itself.

### Agents

| Agent | What it does |
| --- | --- |
| **Tea identifier** | Identifies a tea from a photo, a description, or both. It asks follow-up questions if it needs more detail (packaging, look of the dry leaves, brewed liquor and leaves, taste). It then names the tea and explains why. |
| **Tea researcher** | Given a tea name, researches the optimal steeping time and temperature and forms a consensus from search results. It falls back to general knowledge, and says so, if the search is inconclusive. |
| **Tea sommelier** | Recommends teas. It asks about your mood and flavour preferences, suggests 3 teas, then gives the history and flavour profile of the one you pick, along with 3 food pairings. |

### Using the tea identifier

Start by asking something like `Can you help me identify a tea?` and the supervisor will hand you to the tea identifier.

**Photo upload is not supported yet.** The CLI only sends text, so the identifier can't see images. When it offers the choice between a photo and a verbal description, answer verbally. Describe the tea in as much detail as you can:

- What the packaging says (name, brand, origin, any text or characters)
- What the dry leaves look like (shape, colour, size, aroma)
- What the brewed liquor and wet leaves look like
- What the tea tastes like

The identifier asks follow-up questions if your description isn't enough. If it is still unsure after using what it knows, it searches Google with your clues, then gives you the tea's name and a summary of its reasoning.

### Tools

| Tool | What it does |
| --- | --- |
| `google_tool` | Runs a Google search through SerpAPI for a given query and returns the title, link and snippet of each organic result. All three agents can use it to look up tea information. |
