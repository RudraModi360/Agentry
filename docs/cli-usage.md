# Scratchy CLI Documentation
## *The Command Line Interface*

The CLI is the fastest way to interact with Scratchy. It is perfect for developers who prefer keyboard-first workflows and rapid iteration.

### Launching

Once installed (`pip install -e .`), run:

```bash
agentry
```

### Options

| Flag | Description | Example |
|------|-------------|---------|
| `--session`, `-s` | Resume or create a specific named session | `agentry -s dev-task` |
| `--provider`, `-p` | Select LLM provider (ollama, groq, gemini) | `agentry -p groq` |
| `--model`, `-m` | Specify a model name | `agentry -m llama3-70b` |
| `--attach`, `-a` | Attach files on launch | `agentry -a data.csv` |

### Key Commands (Within TUI)

Once inside the interface, type these slash commands:

- `/new <name>` : Start a fresh session.
- `/attach <path>` : Add file context to the chat.
- `/tools` : List running tools.
- `/quit` : Save and exit.
